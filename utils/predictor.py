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
from datetime import datetime
    

class PredictorComprasMejorado:
    def __init__(self, use_log_transform=True):
        self.model = None
        self.feature_scaler = StandardScaler()
        self.target_scaler = StandardScaler()
        self.use_log_transform = use_log_transform
        self.feature_columns = []
        
    def crear_dataset_mensual(self, df_original):
        """Crear dataset mensual a partir del dataset original - CORREGIDO"""
        df = df_original.copy()
        
        if 'tipo_transac' in df.columns:
            df = df[df['tipo_transac'] != 'SALDO INICIAL']
        
        if len(df) == 0:
            return pd.DataFrame()
        
        df['consumo'] = 0
        if 'canti salida' in df.columns and 'tipo_transac' in df.columns:
            mask_salidas = df['tipo_transac'] == 'SALIDAS'
            df.loc[mask_salidas, 'consumo'] = pd.to_numeric(
                df.loc[mask_salidas, 'canti salida'], errors='coerce'
            ).fillna(0)
        
        if 'fecha' in df.columns:
            df['fecha_dt'] = pd.to_datetime(df['fecha'], errors='coerce', dayfirst=True)
            df.loc[df['fecha_dt'].notna(), 'mes'] = (
                df.loc[df['fecha_dt'].notna(), 'fecha_dt'].dt.year * 100 + 
                df.loc[df['fecha_dt'].notna(), 'fecha_dt'].dt.month
            ).astype(int)
            
            if df['mes'].isna().any():
                df_sin_fecha = df[df['mes'].isna()].copy()
                start_year = 2023
                start_month = 1
                for i, idx in enumerate(df_sin_fecha.index):
                    year = start_year + (start_month + i - 1) // 12
                    month = (start_month + i - 1) % 12 + 1
                    df_sin_fecha.loc[idx, 'mes'] = year * 100 + month
                df.update(df_sin_fecha[['mes']])
        else:
            df = df.reset_index(drop=True)
            start_year = 2023
            start_month = 1
            for i in range(len(df)):
                year = start_year + (start_month + i - 1) // 12
                month = (start_month + i - 1) % 12 + 1
                df.loc[i, 'mes'] = year * 100 + month
        
        if 'mes' not in df.columns:
            return pd.DataFrame()
        
        df['mes'] = pd.to_numeric(df['mes'], errors='coerce').fillna(202301).astype(int)
        
        if 'saldo final' in df.columns:
            df['saldo final'] = pd.to_numeric(df['saldo final'], errors='coerce').fillna(0)
        else:
            df['saldo final'] = 0
        
        df = df[df['id_insumo'].notna()]
        if len(df) == 0:
            return pd.DataFrame()
        
        df_mensual = df.groupby(['id_insumo', 'mes']).agg({
            'consumo': 'sum',
            'saldo final': 'last'
        }).reset_index()
        
        sku_counts = df_mensual['id_insumo'].value_counts()
        skus_validos = sku_counts[sku_counts >= 2].index
        if len(skus_validos) == 0:
            return pd.DataFrame()
        
        df_mensual = df_mensual[df_mensual['id_insumo'].isin(skus_validos)]
        return df_mensual
            
    def preparar_features(self, df_mensual):
        """Preparar características para el modelo"""
        if len(df_mensual) == 0:
            raise ValueError("Dataset mensual está vacío")
            
        df = df_mensual.sort_values(['id_insumo', 'mes']).copy()
        df['año'] = df['mes'] // 100
        df['mes_num'] = df['mes'] % 100
        df['trimestre'] = (df['mes_num'] - 1) // 3 + 1
        
        sku_stats = df.groupby('id_insumo').agg({
            'consumo': ['mean', 'std', 'min', 'max', 'sum'],
            'saldo final': ['mean', 'std', 'min', 'max']
        }).round(2)
        
        sku_stats.columns = ['_'.join(col).strip() for col in sku_stats.columns.values]
        sku_stats = sku_stats.reset_index()
        df = df.merge(sku_stats, on='id_insumo', how='left')
        
        for lag in [1, 2, 3]:
            df[f'consumo_lag_{lag}'] = df.groupby('id_insumo')['consumo'].shift(lag)
            df[f'saldo_lag_{lag}'] = df.groupby('id_insumo')['saldo final'].shift(lag)
        
        df['consumo_rolling_mean_3'] = df.groupby('id_insumo')['consumo'].transform(
            lambda x: x.rolling(3, min_periods=1).mean()
        )
        
        df['es_fin_ano'] = df['mes_num'].isin([11, 12, 1])
        df['es_inicio_ano'] = df['mes_num'].isin([1, 2, 3])
        df['dias_inventario'] = np.where(
            df['consumo_mean'] > 0,
            (df['saldo final'] / (df['consumo_mean'] / 30)),
            0
        )
        
        self.feature_columns = [
            'mes_num', 'trimestre', 'es_fin_ano', 'es_inicio_ano',
            'consumo_mean', 'consumo_std', 'consumo_min', 'consumo_max',
            'consumo_lag_1', 'consumo_lag_2', 'consumo_lag_3',
            'saldo_lag_1', 'saldo_lag_2', 'saldo_lag_3',
            'consumo_rolling_mean_3', 'dias_inventario'
        ]
        
        self.feature_columns = [col for col in self.feature_columns if col in df.columns]
        df_clean = df.dropna(subset=self.feature_columns)
        return df_clean
    
    def transformar_target(self, y):
        if self.use_log_transform:
            return np.log1p(y)
        else:
            return self.target_scaler.fit_transform(y.values.reshape(-1, 1)).flatten()
    
    def revertir_target(self, y_transformed):
        if self.use_log_transform:
            return np.expm1(y_transformed)
        else:
            return self.target_scaler.inverse_transform(y_transformed.reshape(-1, 1)).flatten()
    
    def entrenar_modelo(self, df_preparado):
        if len(df_preparado) == 0:
            raise ValueError("No hay datos suficientes")
            
        X = df_preparado[self.feature_columns]
        y_original = df_preparado['consumo']
        y_transformed = self.transformar_target(y_original)
        
        if len(X) < 10:
            X_train, X_test = X, X
            y_train, y_test_original = y_transformed, y_original
            y_test = y_original
        else:
            indices = df_preparado.index
            X_train, X_test, y_train, y_test, indices_train, indices_test = train_test_split(
                X, y_original, indices, test_size=0.2, random_state=42
            )
            y_train_transformed = self.transformar_target(y_train)
            y_test_original = y_test
        
        X_train_scaled = self.feature_scaler.fit_transform(X_train)
        rf_model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
        gb_model = GradientBoostingRegressor(n_estimators=100, random_state=42, max_depth=6)
        
        rf_model.fit(X_train_scaled, y_train_transformed)
        gb_model.fit(X_train_scaled, y_train_transformed)
        self.model = {'rf': rf_model, 'gb': gb_model}
        
        if len(X_test) > 0:
            X_test_scaled = self.feature_scaler.transform(X_test)
            y_pred_rf_transformed = rf_model.predict(X_test_scaled)
            y_pred_gb_transformed = gb_model.predict(X_test_scaled)
            y_pred_ensemble_transformed = (y_pred_rf_transformed + y_pred_gb_transformed) / 2
            y_pred_ensemble_original = self.revertir_target(y_pred_ensemble_transformed)
            mae = mean_absolute_error(y_test_original, y_pred_ensemble_original)
            rmse = np.sqrt(mean_squared_error(y_test_original, y_pred_ensemble_original))
            mask = y_test_original != 0
            y_real_nonzero = y_test_original[mask]
            y_pred_nonzero = y_pred_ensemble_original[mask]
            if len(y_real_nonzero) > 0:
                mape = np.mean(np.abs((y_real_nonzero - y_pred_nonzero) / y_real_nonzero)) * 100
                within_20pct = np.mean(np.abs((y_real_nonzero - y_pred_nonzero) / y_real_nonzero) <= 0.20) * 100
            else:
                mape = np.nan
                within_20pct = np.nan
            errores = np.abs(y_test_original - y_pred_ensemble_original)
        
        return self.model
    
    def predecir_trimestral(self, df_preparado):
        try:
            resultados_mensuales = []
            for mes in range(1, 4):
                resultado_mes = self.calcular_cantidad_comprar(df_preparado)
                resultado_mes['mes_del_trimestre'] = mes
                resultados_mensuales.append(resultado_mes)
            df_trimestral = pd.concat(resultados_mensuales, ignore_index=True)
            resultados_agrupados = df_trimestral.groupby('id_insumo').agg({
                'consumo_predicho': 'sum',
                'cantidad_comprar': 'sum',
                'saldo final': 'last',
                'prioridad': 'first'
            }).reset_index()
            resultados_agrupados['consumo_trimestral_predicho'] = resultados_agrupados['consumo_predicho']
            resultados_agrupados['cantidad_comprar_trimestral'] = resultados_agrupados['cantidad_comprar']
            return resultados_agrupados
        except Exception as e:
            return pd.DataFrame()

    def predecir_anual(self, df_preparado):
        try:
            resultados_mensuales = []
            for mes in range(1, 13):
                resultado_mes = self.calcular_cantidad_comprar(df_preparado)
                resultado_mes['mes_del_año'] = mes
                resultados_mensuales.append(resultado_mes)
            df_anual = pd.concat(resultados_mensuales, ignore_index=True)
            resultados_agrupados = df_anual.groupby('id_insumo').agg({
                'consumo_predicho': 'sum',
                'cantidad_comprar': 'sum',
                'saldo final': 'last',
                'prioridad': 'first'
            }).reset_index()
            resultados_agrupados['consumo_anual_predicho'] = resultados_agrupados['consumo_predicho']
            resultados_agrupados['cantidad_comprar_anual'] = resultados_agrupados['cantidad_comprar']
            return resultados_agrupados
        except Exception as e:
            return pd.DataFrame()
    
    def calcular_cantidad_comprar(self, df_preparado, lead_time_dias=30, nivel_servicio=0.95):
        if self.model is None:
            raise ValueError("El modelo debe ser entrenado primero")
        
        df_resultados = df_preparado.copy()
        X = df_resultados[self.feature_columns]
        X_scaled = self.feature_scaler.transform(X)
        pred_rf = self.model['rf'].predict(X_scaled)
        pred_gb = self.model['gb'].predict(X_scaled)
        consumo_predicho_transformed = (pred_rf + pred_gb) / 2
        consumo_predicho = self.revertir_target(consumo_predicho_transformed)
        df_resultados['consumo_predicho'] = consumo_predicho
        df_resultados['cantidad_comprar'] = self._calcular_recomendacion_compra(
            df_resultados, lead_time_dias, nivel_servicio
        )
        df_resultados = self._generar_recomendaciones(df_resultados)
        df_agrupado = df_resultados.groupby('id_insumo').agg({
            'consumo_predicho': 'mean',
            'cantidad_comprar': 'sum',
            'saldo final': 'last',
            'recomendacion': lambda x: x.iloc[-1],
            'prioridad': lambda x: x.iloc[-1]
        }).reset_index()
        return df_agrupado
        
    def _calcular_recomendacion_compra(self, df, lead_time, nivel_servicio):
        z_score = 1.645 if nivel_servicio == 0.95 else 1.282
        demanda_std = df['consumo_std'].fillna(df['consumo_mean'] * 0.3)
        demanda_std = np.where(demanda_std == 0, df['consumo_mean'] * 0.1, demanda_std)
        stock_seguridad = z_score * demanda_std * np.sqrt(lead_time / 30)
        inventario_objetivo = df['consumo_predicho'] + stock_seguridad
        cantidad_comprar = inventario_objetivo - df['saldo final']
        cantidad_comprar = np.where(cantidad_comprar < 0, 0, cantidad_comprar)
        cantidad_comprar = np.maximum(cantidad_comprar, 0)
        cantidad_comprar = np.ceil(cantidad_comprar)
        return cantidad_comprar
    
    def _generar_recomendaciones(self, df):
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
        os.makedirs(ruta, exist_ok=True)
        joblib.dump(self.model, f'{ruta}modelo_ensemble.pkl')
        joblib.dump(self.feature_scaler, f'{ruta}feature_scaler.pkl')
        joblib.dump(self.target_scaler, f'{ruta}target_scaler.pkl')
        joblib.dump(self.feature_columns, f'{ruta}feature_columns.pkl')
        joblib.dump(self.use_log_transform, f'{ruta}config.pkl')
    
    def cargar_modelo(self, ruta='modelo_compras/'):
        try:
            self.model = joblib.load(f'{ruta}modelo_ensemble.pkl')
            self.feature_scaler = joblib.load(f'{ruta}feature_scaler.pkl')
            self.target_scaler = joblib.load(f'{ruta}target_scaler.pkl')
            self.feature_columns = joblib.load(f'{ruta}feature_columns.pkl')
            self.use_log_transform = joblib.load(f'{ruta}config.pkl')
            return True
        except FileNotFoundError:
            return False
    
    def obtener_fechas_prediccion_futura(self, periodo="mensual"):
        hoy = datetime.now()
        año_actual = hoy.year
        mes_actual = hoy.month
        
        if periodo == "mensual":
            próximo_mes = mes_actual + 1
            próximo_año = año_actual
            if próximo_mes > 12:
                próximo_mes = 1
                próximo_año = año_actual + 1
            return [f"{próximo_año}-{próximo_mes:02d}"]
        
        elif periodo == "trimestral":
            fechas = []
            for i in range(1, 4):
                mes = mes_actual + i
                año = año_actual
                if mes > 12:
                    mes = mes - 12
                    año = año_actual + 1
                fechas.append(f"{año}-{mes:02d}")
            return fechas
        
        elif periodo == "anual":
            fechas = []
            for i in range(1, 13):
                mes = mes_actual + i
                año = año_actual
                if mes > 12:
                    mes = mes - 12
                    año = año_actual + 1
                fechas.append(f"{año}-{mes:02d}")
            return fechas
