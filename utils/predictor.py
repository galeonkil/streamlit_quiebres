import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
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
        
    def crear_dataset_mensual(self, df_original):
        """Crear dataset mensual a partir del dataset original"""
        print("Creando dataset mensual...")
        
        # Hacer una copia para no modificar el original
        df = df_original.copy()
        
        # Manejar fechas de manera robusta
        if 'fecha' in df.columns:
            print("Procesando columna 'fecha'...")
            df['fecha_dt'] = pd.to_datetime(df['fecha'], errors='coerce', dayfirst=True)
            
            # Para fechas válidas, crear mes
            df.loc[df['fecha_dt'].notna(), 'mes'] = (
                df.loc[df['fecha_dt'].notna(), 'fecha_dt'].dt.year * 100 + 
                df.loc[df['fecha_dt'].notna(), 'fecha_dt'].dt.month
            ).astype(int)
            
            # Para fechas inválidas, crear meses secuenciales
            if df['mes'].isna().any():
                print("Creando meses secuenciales...")
                df_sin_fecha = df[df['mes'].isna()].copy()
                
                start_year = 2023
                start_month = 1
                for i, idx in enumerate(df_sin_fecha.index):
                    year = start_year + (start_month + i - 1) // 12
                    month = (start_month + i - 1) % 12 + 1
                    df_sin_fecha.loc[idx, 'mes'] = year * 100 + month
                
                df.update(df_sin_fecha[['mes']])
        
        else:
            # Si no hay columna fecha, crear meses secuenciales
            print("Creando meses secuenciales...")
            df = df.reset_index(drop=True)
            start_year = 2023
            start_month = 1
            for i in range(len(df)):
                year = start_year + (start_month + i - 1) // 12
                month = (start_month + i - 1) % 12 + 1
                df.loc[i, 'mes'] = year * 100 + month
        
        # Asegurar que mes es numérico
        df['mes'] = pd.to_numeric(df['mes'], errors='coerce').fillna(202301).astype(int)
        
        # Calcular consumo
        if 'canti salida' in df.columns:
            df['consumo'] = pd.to_numeric(df['canti salida'], errors='coerce').fillna(0)
        elif 'consumo' in df.columns:
            df['consumo'] = pd.to_numeric(df['consumo'], errors='coerce').fillna(0)
        else:
            df['consumo'] = 0
        
        # Manejar saldo final
        if 'saldo final' in df.columns:
            df['saldo final'] = pd.to_numeric(df['saldo final'], errors='coerce').fillna(0)
        else:
            df['saldo final'] = 0
        
        # Filtrar solo registros con id_insumo válido
        df = df[df['id_insumo'].notna()]
        
        # Agrupar por mes y SKU
        df_mensual = df.groupby(['id_insumo', 'mes']).agg({
            'consumo': 'sum',
            'saldo final': 'last'
        }).reset_index()
        
        # Filtrar SKUs con suficiente historial
        sku_counts = df_mensual['id_insumo'].value_counts()
        skus_validos = sku_counts[sku_counts >= 2].index
        df_mensual = df_mensual[df_mensual['id_insumo'].isin(skus_validos)]
        
        print(f"Dataset mensual creado: {len(df_mensual)} registros")
        print(f"SKUs válidos: {df_mensual['id_insumo'].nunique()}")
        
        return df_mensual
    
    def preparar_features(self, df_mensual):
        """Preparar características para el modelo"""
        if len(df_mensual) == 0:
            raise ValueError("Dataset mensual está vacío")
            
        df = df_mensual.sort_values(['id_insumo', 'mes']).copy()
        
        # Crear características temporales
        df['año'] = df['mes'] // 100
        df['mes_num'] = df['mes'] % 100
        df['trimestre'] = (df['mes_num'] - 1) // 3 + 1
        
        # Calcular métricas por SKU
        sku_stats = df.groupby('id_insumo').agg({
            'consumo': ['mean', 'std', 'min', 'max', 'sum'],
            'saldo final': ['mean', 'std', 'min', 'max']
        }).round(2)
        
        sku_stats.columns = ['_'.join(col).strip() for col in sku_stats.columns.values]
        sku_stats = sku_stats.reset_index()
        
        # Unir estadísticas al dataframe principal
        df = df.merge(sku_stats, on='id_insumo', how='left')
        
        # Crear variables lag
        for lag in [1, 2, 3]:
            df[f'consumo_lag_{lag}'] = df.groupby('id_insumo')['consumo'].shift(lag)
            df[f'saldo_lag_{lag}'] = df.groupby('id_insumo')['saldo final'].shift(lag)
        
        # Calcular tendencias
        df['consumo_rolling_mean_3'] = df.groupby('id_insumo')['consumo'].transform(
            lambda x: x.rolling(3, min_periods=1).mean()
        )
        
        # Identificar patrones estacionales
        df['es_fin_ano'] = df['mes_num'].isin([11, 12, 1])
        df['es_inicio_ano'] = df['mes_num'].isin([1, 2, 3])
        
        # Calcular métricas de inventario
        df['dias_inventario'] = np.where(
            df['consumo_mean'] > 0,
            (df['saldo final'] / (df['consumo_mean'] / 30)),
            0
        )
        
        # Características para el modelo
        self.feature_columns = [
            'mes_num', 'trimestre', 'es_fin_ano', 'es_inicio_ano',
            'consumo_mean', 'consumo_std', 'consumo_min', 'consumo_max',
            'consumo_lag_1', 'consumo_lag_2', 'consumo_lag_3',
            'saldo_lag_1', 'saldo_lag_2', 'saldo_lag_3',
            'consumo_rolling_mean_3', 'dias_inventario'
        ]
        
        # Filtrar solo columnas que existen
        self.feature_columns = [col for col in self.feature_columns if col in df.columns]
        
        # Eliminar filas con NaN en las características
        df_clean = df.dropna(subset=self.feature_columns)
        
        print(f"Registros para entrenamiento: {len(df_clean)}")
        print(f"SKUs para entrenamiento: {df_clean['id_insumo'].nunique()}")
        
        return df_clean
    
    def transformar_target(self, y):
        """Transformar el target para manejar outliers"""
        if self.use_log_transform:
            # Log transformation: maneja grandes variaciones
            return np.log1p(y)  # log(1 + x) para evitar log(0)
        else:
            # Standard scaling
            return self.target_scaler.fit_transform(y.values.reshape(-1, 1)).flatten()
    
    def revertir_target(self, y_transformed):
        """Revertir la transformación del target"""
        if self.use_log_transform:
            return np.expm1(y_transformed)  # exp(x) - 1
        else:
            return self.target_scaler.inverse_transform(y_transformed.reshape(-1, 1)).flatten()
    
    def entrenar_modelo(self, df_preparado):
        """Entrenar el modelo con target transformado"""
        if len(df_preparado) == 0:
            raise ValueError("No hay datos suficientes")
            
        X = df_preparado[self.feature_columns]
        y_original = df_preparado['consumo']
        
        print("=" * 50)
        print("ESTADÍSTICAS DEL CONSUMO ORIGINAL:")
        print(f"Media: {y_original.mean():.2f}")
        print(f"Desviación estándar: {y_original.std():.2f}")
        print(f"Mínimo: {y_original.min():.2f}")
        print(f"Máximo: {y_original.max():.2f}")
        print(f"Percentil 95: {np.percentile(y_original, 95):.2f}")
        print("=" * 50)
        
        # Transformar target
        y_transformed = self.transformar_target(y_original)
        
        print("ESTADÍSTICAS DEL CONSUMO TRANSFORMADO:")
        print(f"Media: {y_transformed.mean():.2f}")
        print(f"Desviación estándar: {y_transformed.std():.2f}")
        print(f"Mínimo: {y_transformed.min():.2f}")
        print(f"Máximo: {y_transformed.max():.2f}")
        print("=" * 50)
        
        # CORREGIDO: Manejo correcto del train/test split
        if len(X) < 10:
            print("Pocos datos, usando todos para entrenamiento y prueba")
            X_train, X_test = X, X
            y_train, y_test_original = y_transformed, y_original
            y_test = y_original
        else:
            # Hacer split manteniendo índices
            indices = df_preparado.index
            X_train, X_test, y_train, y_test, indices_train, indices_test = train_test_split(
                X, y_original, indices, test_size=0.2, random_state=42
            )
            y_train_transformed = self.transformar_target(y_train)
            y_test_original = y_test
        
        # Escalar características
        X_train_scaled = self.feature_scaler.fit_transform(X_train)
        
        # Entrenar modelos
        rf_model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
        gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42, max_depth=6)
        
        rf_model.fit(X_train_scaled, y_train_transformed)
        gb_model.fit(X_train_scaled, y_train_transformed)
        
        self.model = {'rf': rf_model, 'gb': gb_model}
        
        # Evaluar modelo
        if len(X_test) > 0:
            X_test_scaled = self.feature_scaler.transform(X_test)
            
            # Predicciones individuales
            y_pred_rf_transformed = rf_model.predict(X_test_scaled)
            y_pred_gb_transformed = gb_model.predict(X_test_scaled)
            
            # Ensemble
            y_pred_ensemble_transformed = (y_pred_rf_transformed + y_pred_gb_transformed) / 2
            
            # Revertir a escala original
            y_pred_ensemble_original = self.revertir_target(y_pred_ensemble_transformed)
            
            # Calcular métricas
            mae = mean_absolute_error(y_test_original, y_pred_ensemble_original)
            rmse = np.sqrt(mean_squared_error(y_test_original, y_pred_ensemble_original))
            
            # Calcular MAPE
            mask = y_test_original != 0
            y_real_nonzero = y_test_original[mask]
            y_pred_nonzero = y_pred_ensemble_original[mask]
            
            if len(y_real_nonzero) > 0:
                mape = np.mean(np.abs((y_real_nonzero - y_pred_nonzero) / y_real_nonzero)) * 100
                within_20pct = np.mean(np.abs((y_real_nonzero - y_pred_nonzero) / y_real_nonzero) <= 0.20) * 100
            else:
                mape = np.nan
                within_20pct = np.nan
            
            print("=== RESULTADOS MEJORADOS ===")
            print(f"MAE: {mae:.2f}")
            print(f"RMSE: {rmse:.2f}")
            print(f"MAPE: {mape:.1f}%")
            print(f"Predicciones dentro del ±20%: {within_20pct:.1f}%")
            
            # Análisis de errores
            errores = np.abs(y_test_original - y_pred_ensemble_original)
            print(f"Error máximo: {errores.max():.2f}")
            print(f"Percentil 95 de errores: {np.percentile(errores, 95):.2f}")
            print(f"SKUs con error > 100: {(errores > 100).sum()}")
        
        return self.model
    
    def calcular_cantidad_comprar(self, df_preparado, lead_time_dias=30, nivel_servicio=0.95):
        """Calcular cuánto comprar cada mes para cada SKU"""
        if self.model is None:
            raise ValueError("El modelo debe ser entrenado primero")
        
        df_resultados = df_preparado.copy()
        
        # Preparar características para predicción
        X = df_resultados[self.feature_columns]
        X_scaled = self.feature_scaler.transform(X)
        
        # Predecir consumo (en escala transformada)
        pred_rf = self.model['rf'].predict(X_scaled)
        pred_gb = self.model['gb'].predict(X_scaled)
        consumo_predicho_transformed = (pred_rf + pred_gb) / 2
        
        # Revertir a escala original
        consumo_predicho = self.revertir_target(consumo_predicho_transformed)
        
        df_resultados['consumo_predicho'] = consumo_predicho
        
        # Calcular cantidad a comprar
        df_resultados['cantidad_comprar'] = self._calcular_recomendacion_compra(
            df_resultados, lead_time_dias, nivel_servicio
        )
        
        # Identificar recomendaciones específicas
        df_resultados = self._generar_recomendaciones(df_resultados)
        
        return df_resultados
    
    def _calcular_recomendacion_compra(self, df, lead_time, nivel_servicio):
        """Calcular la cantidad específica a comprar"""
        # Z-score para nivel de servicio
        z_score = 1.645 if nivel_servicio == 0.95 else 1.282
        
        # Stock de seguridad (manejar casos donde std es 0)
        demanda_std = df['consumo_std'].fillna(df['consumo_mean'] * 0.3)
        demanda_std = np.where(demanda_std == 0, df['consumo_mean'] * 0.1, demanda_std)
        
        stock_seguridad = z_score * demanda_std * np.sqrt(lead_time / 30)
        
        # Inventario objetivo = consumo predicho + stock seguridad
        inventario_objetivo = df['consumo_predicho'] + stock_seguridad
        
        # Cantidad a comprar = Inventario objetivo - Stock actual
        cantidad_comprar = inventario_objetivo - df['saldo final']
        
        # No comprar si ya tenemos suficiente stock
        cantidad_comprar = np.where(
            cantidad_comprar < 0, 
            0,
            cantidad_comprar
        )
        
        # Aplicar reglas de redondeo
        cantidad_comprar = np.maximum(cantidad_comprar, 0)
        cantidad_comprar = np.ceil(cantidad_comprar)
        
        return cantidad_comprar
    
    def _generar_recomendaciones(self, df):
        """Generar recomendaciones específicas de compra"""
        condiciones = [
            (df['cantidad_comprar'] == 0) & (df['saldo final'] > df['consumo_predicho'] * 2),
            (df['cantidad_comprar'] == 0) & (df['saldo final'] > df['consumo_predicho']),
            (df['cantidad_comprar'] > 0) & (df['cantidad_comprar'] <= df['consumo_predicho'] * 0.5),
            (df['cantidad_comprar'] > df['consumo_predicho'] * 0.5) & (df['cantidad_comprar'] <= df['consumo_predicho'] * 1.5),
            (df['cantidad_comprar'] > df['consumo_predicho'] * 1.5)
        ]
        
        opciones = [
            'NO COMPRAR - Exceso de stock',
            'NO COMPRAR - Stock suficiente',
            'COMPRAR MÍNIMO - Reposición básica',
            'COMPRAR NORMAL - Demanda esperada',
            'COMPRAR EXTRA - Alta demanda/stock bajo'
        ]
        
        df['recomendacion'] = np.select(condiciones, opciones, default='REVISAR')
        
        # Calcular prioridad
        df['prioridad'] = np.where(
            (df['saldo final'] < df['consumo_predicho'] * 0.3) & (df['consumo_predicho'] > 0),
            'ALTA',
            np.where(
                df['saldo final'] > df['consumo_predicho'] * 3,
                'BAJA',
                'MEDIA'
            )
        )
        
        return df

    def guardar_modelo(self, ruta='modelo_compras/'):
        """Guardar el modelo entrenado para uso futuro"""
        # Crear directorio si no existe
        os.makedirs(ruta, exist_ok=True)
        
        # Guardar componentes del modelo
        joblib.dump(self.model, f'{ruta}modelo_ensemble.pkl')
        joblib.dump(self.feature_scaler, f'{ruta}feature_scaler.pkl')
        joblib.dump(self.target_scaler, f'{ruta}target_scaler.pkl')
        joblib.dump(self.feature_columns, f'{ruta}feature_columns.pkl')
        joblib.dump(self.use_log_transform, f'{ruta}config.pkl')
        
        print(f"✅ Modelo guardado en: {ruta}")
        print("📁 Archivos creados:")
        print(f"   - modelo_ensemble.pkl (modelos RF y GB)")
        print(f"   - feature_scaler.pkl (escalador de características)")
        print(f"   - target_scaler.pkl (escalador de target)") 
        print(f"   - feature_columns.pkl (columnas usadas)")
        print(f"   - config.pkl (configuración)")
    
    def cargar_modelo(self, ruta='modelo_compras/'):
        """Cargar modelo pre-entrenado"""
        try:
            self.model = joblib.load(f'{ruta}modelo_ensemble.pkl')
            self.feature_scaler = joblib.load(f'{ruta}feature_scaler.pkl')
            self.target_scaler = joblib.load(f'{ruta}target_scaler.pkl')
            self.feature_columns = joblib.load(f'{ruta}feature_columns.pkl')
            self.use_log_transform = joblib.load(f'{ruta}config.pkl')
            
            print(f"✅ Modelo cargado desde: {ruta}")
            print(f"📊 Modelo listo para hacer predicciones")
            return True
            
        except FileNotFoundError:
            print(f"❌ No se encontraron archivos del modelo en {ruta}")
            print("💡 Ejecuta primero: predictor.guardar_modelo()")
            return False