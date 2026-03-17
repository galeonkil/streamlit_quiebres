import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

class PredictorComprasMejorado:
    def __init__(self, use_log_transform=True):
        self.model = None
        self.feature_scaler = StandardScaler()
        self.target_scaler = StandardScaler()
        self.use_log_transform = use_log_transform
        self.feature_columns = []
        self.is_trained = False

    def cargar_datos_procesados(self, ruta='dataset_mensual_generado.xlsx'):
        """Carga el dataset ya procesado desde Excel."""
        print(f"📂 Cargando datos procesados desde: {ruta}")
        df = pd.read_excel(ruta)
        print(f"✅ Datos cargados: {len(df)} registros, {df['producto_estado'].nunique()} productos")
        return df

    # ==============================
    # Preparar características para el modelo
    # ==============================
    def preparar_features(self, df_vertical):
        """Preparar características para el modelo de ML"""
        if len(df_vertical) == 0:
            raise ValueError("Dataset vertical está vacío")
        
        df = df_vertical.copy()
        
        # Ordenar por producto y mes
        df = df.sort_values(['producto_estado', 'mes']).copy()
        
        # Extraer información del mes
        df['año'] = df['mes'] // 100
        df['mes_num'] = df['mes'] % 100
        df['trimestre'] = (df['mes_num'] - 1) // 3 + 1
        
        # Estadísticas de consumo por producto
        consumo_stats = df.groupby('producto_estado')['consumo'].agg([
            'mean', 'std', 'min', 'max', 'sum', 'count'
        ]).round(2)
        consumo_stats.columns = [f'consumo_{col}' for col in consumo_stats.columns]
        
        df = df.merge(consumo_stats, on='producto_estado', how='left')
        
        # Lags de consumo
        for lag in [1, 2]:
            df[f'consumo_lag_{lag}'] = df.groupby('producto_estado')['consumo'].shift(lag)
        
        # Ventanas móviles
        df['consumo_rolling_mean_3'] = df.groupby('producto_estado')['consumo'].transform(
            lambda x: x.rolling(3, min_periods=1).mean()
        )
        
        df['consumo_rolling_std_3'] = df.groupby('producto_estado')['consumo'].transform(
            lambda x: x.rolling(3, min_periods=1).std()
        )
        
        # Características temporales
        df['es_fin_ano'] = df['mes_num'].isin([11, 12, 1]).astype(int)
        df['es_inicio_ano'] = df['mes_num'].isin([1, 2, 3]).astype(int)
        df['es_mitad_ano'] = df['mes_num'].isin([6, 7, 8]).astype(int)
        
        # Estacionalidad
        df['estacionalidad_mes'] = df['mes_num'] / 12
        
        # Tendencia y variación
        df['tendencia_consumo'] = df.groupby('producto_estado')['consumo'].transform(
            lambda x: x.diff().rolling(2, min_periods=1).mean()
        )
        
        df['variacion_mensual'] = df.groupby('producto_estado')['consumo'].transform(
            lambda x: x.pct_change().replace([np.inf, -np.inf], 0)
        )
        
        df['consumo_creciente'] = (df['tendencia_consumo'] > 0).astype(int)
        
        # Características de inventario
        df['nivel_inventario_pct'] = df['inventario_actual'] / (df['inventario_optimo'] + 1)
        df['necesidad_compra'] = (df['inventario_optimo'] - df['inventario_actual']).clip(lower=0)
        df['sobre_stock'] = (df['inventario_actual'] - df['inventario_optimo']).clip(lower=0)
        
        # Estado codificado
        estado_map = {'QUIEBRE': 0, 'OPTIMO': 1, 'SOBRE STOCK': 2}
        df['estado_cod'] = df['estado'].map(estado_map).fillna(1)
        
        # Limpiar valores
        df = df.replace([np.inf, -np.inf], np.nan)
        
        # Definir columnas de características
        self.feature_columns = [
            'mes_num', 'trimestre', 'es_fin_ano', 'es_inicio_ano', 'es_mitad_ano',
            'estacionalidad_mes', 'consumo_creciente',
            'consumo_mean', 'consumo_std', 'consumo_min', 'consumo_max',
            'consumo_lag_1', 'consumo_lag_2',
            'consumo_rolling_mean_3', 'consumo_rolling_std_3',
            'tendencia_consumo', 'variacion_mensual',
            'nivel_inventario_pct', 'necesidad_compra', 'sobre_stock',
            'estado_cod', 'diferencia', 'stock_seguridad'
        ]
        
        # Solo mantener columnas que existen
        self.feature_columns = [col for col in self.feature_columns if col in df.columns]
        
        # Rellenar valores faltantes
        for col in self.feature_columns:
            if df[col].dtype in [np.float64, np.int64]:
                if col.startswith('consumo_'):
                    df[col] = df[col].fillna(df['consumo_mean'])
                elif 'lag' in col:
                    df[col] = df[col].fillna(df['consumo'])
                else:
                    df[col] = df[col].fillna(0)
        
        # Asegurar que tenemos todas las columnas necesarias
        df_clean = df.dropna(subset=self.feature_columns + ['consumo'])
        
        return df_clean
    
    # ==============================
    # Transformar target
    # ==============================
    def transformar_target(self, y, fit_scaler=True):
        """Transformar variable objetivo"""
        if self.use_log_transform:
            return np.log1p(y)
        else:
            y_reshaped = y.values.reshape(-1, 1) if hasattr(y, 'values') else y.reshape(-1, 1)
            if fit_scaler:
                return self.target_scaler.fit_transform(y_reshaped).flatten()
            else:
                return self.target_scaler.transform(y_reshaped).flatten()
    
    def revertir_target(self, y_transformed):
        """Revertir transformación de variable objetivo"""
        if self.use_log_transform:
            return np.expm1(y_transformed)
        else:
            y_reshaped = y_transformed.reshape(-1, 1) if len(y_transformed.shape) == 1 else y_transformed
            return self.target_scaler.inverse_transform(y_reshaped).flatten()
    
    # ==============================
    # Entrenar modelo
    # ==============================
    def entrenar_modelo(self, df_preparado):
        """Entrenar modelo con datos preparados"""
        if len(df_preparado) == 0:
            raise ValueError("No hay datos suficientes")
        
        X = df_preparado[self.feature_columns]
        y_original = df_preparado['consumo']
        
        # Transformar target - ajustar scaler en entrenamiento
        y_transformed = self.transformar_target(y_original, fit_scaler=True)
        
        # Dividir datos si hay suficientes
        if len(X) < 10:
            X_train = X
            y_train = y_transformed
            X_test = X
            y_test = y_original
        else:
            # Usar train_test_split con índices para mantener consistencia
            indices = range(len(X))
            train_idx, test_idx = train_test_split(indices, test_size=0.2, random_state=42)
            
            X_train = X.iloc[train_idx]
            X_test = X.iloc[test_idx]
            y_train_original = y_original.iloc[train_idx]
            y_test_original = y_original.iloc[test_idx]
            
            # Transformar solo train para ajustar scaler
            y_train = self.transformar_target(y_train_original, fit_scaler=True)
            y_test = self.transformar_target(y_test_original, fit_scaler=False)
        
        # Escalar features
        X_train_scaled = self.feature_scaler.fit_transform(X_train)
        
        # Crear y entrenar modelos
        rf_model = RandomForestRegressor(
            n_estimators=100, 
            random_state=42, 
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2
        )
        
        gb_model = GradientBoostingRegressor(
            n_estimators=100, 
            random_state=42, 
            max_depth=6,
            learning_rate=0.1
        )
        
        # Entrenar modelos
        rf_model.fit(X_train_scaled, y_train)
        gb_model.fit(X_train_scaled, y_train)
        
        # Guardar modelo
        self.model = {
            'rf': rf_model,
            'gb': gb_model
        }
        self.is_trained = True
        
        # Calcular métricas si hay test
        if len(X) >= 10:
            X_test_scaled = self.feature_scaler.transform(X_test)
            
            # Predicciones en test
            pred_rf = self.model['rf'].predict(X_test_scaled)
            pred_gb = self.model['gb'].predict(X_test_scaled)
            pred_ensemble = (pred_rf + pred_gb) / 2
            
            # Revertir transformaciones
            y_test_reverted = self.revertir_target(y_test)
            pred_reverted = self.revertir_target(pred_ensemble)
            
            # Métricas
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
            
            mae = mean_absolute_error(y_test_reverted, pred_reverted)
            rmse = np.sqrt(mean_squared_error(y_test_reverted, pred_reverted))
            r2 = r2_score(y_test_reverted, pred_reverted)
            
            metrics = {
                'MAE': mae,
                'RMSE': rmse,
                'R2': r2
            }
            
            return self.model, metrics
        
        return self.model, {}
    
    # ==============================
    # Predecir consumo
    # ==============================
    def predecir_consumo(self, df_preparado):
        """Predecir consumo basado en datos históricos (sin fechas futuras)"""
        if self.model is None or not self.is_trained:
            raise ValueError("El modelo debe ser entrenado primero")
        
        predicciones = []
        
        for producto in df_preparado['producto_estado'].unique():
            # 1. Obtener datos históricos de este producto
            df_producto = df_preparado[df_preparado['producto_estado'] == producto]
            
            if len(df_producto) == 0:
                continue
            
            # 2. Tomar el ÚLTIMO registro (marzo) como base
            ultimo_registro = df_producto.iloc[-1].copy()
            
            # 3. Crear datos de predicción con características ACTUALES
            datos_prediccion = {}
            
            # 3.1. Copiar características que ya están calculadas
            for col in self.feature_columns:
                if col in ultimo_registro.index:
                    datos_prediccion[col] = ultimo_registro[col]
                else:
                    datos_prediccion[col] = 0
            
            # 4. Preparar datos para predicción
            X_pred = pd.DataFrame([datos_prediccion])[self.feature_columns]
            
            # 5. Escalar y predecir
            X_pred_scaled = self.feature_scaler.transform(X_pred)
            
            pred_rf = self.model['rf'].predict(X_pred_scaled)[0]
            pred_gb = self.model['gb'].predict(X_pred_scaled)[0]
            consumo_predicho_transformed = (pred_rf + pred_gb) / 2
            
            # Revertir transformación
            consumo_predicho = self.revertir_target(consumo_predicho_transformed)
            consumo_predicho = max(0, consumo_predicho)  # No puede ser negativo
            
            # 6. Guardar resultado SIMPLE
            predicciones.append({
                'producto_estado': producto,
                'descripcion': ultimo_registro.get('descripcion', ''),
                'consumo_historial_promedio': ultimo_registro.get('consumo_mean', 0),
                'consumo_ultimo_mes': ultimo_registro.get('consumo', 0),
                'consumo_predicho': round(consumo_predicho, 2),
                'precio_unitario': ultimo_registro.get('precio_unitario', 0)
            })
        
        df_predicciones = pd.DataFrame(predicciones)
        return df_predicciones
    
    # ==============================
    # Guardar y cargar modelo
    # ==============================
    def guardar_modelo(self, ruta='modelo_compras/'):
        """Guardar modelo entrenado"""
        os.makedirs(ruta, exist_ok=True)
        
        joblib.dump(self.model, f'{ruta}modelo_ensemble.pkl')
        joblib.dump(self.feature_scaler, f'{ruta}feature_scaler.pkl')
        joblib.dump(self.target_scaler, f'{ruta}target_scaler.pkl')
        joblib.dump(self.feature_columns, f'{ruta}feature_columns.pkl')
        joblib.dump(self.use_log_transform, f'{ruta}config.pkl')
        
        print(f"✅ Modelo guardado en: {ruta}")
    
    def cargar_modelo(self, ruta='modelo_compras/'):
        """Cargar modelo previamente entrenado"""
        try:
            self.model = joblib.load(f'{ruta}modelo_ensemble.pkl')
            self.feature_scaler = joblib.load(f'{ruta}feature_scaler.pkl')
            self.target_scaler = joblib.load(f'{ruta}target_scaler.pkl')
            self.feature_columns = joblib.load(f'{ruta}feature_columns.pkl')
            self.use_log_transform = joblib.load(f'{ruta}config.pkl')
            self.is_trained = True
            
            print(f"✅ Modelo cargado desde: {ruta}")
            return True
        except Exception as e:
            print(f"❌ Error al cargar modelo: {e}")
            return False