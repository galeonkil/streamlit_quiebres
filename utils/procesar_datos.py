import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os
import warnings
warnings.filterwarnings('ignore')
import difflib   # <--- agregado para similitud

# ==============================================
# CLASE PREDICTOR COMPLETA Y CORREGIDA
# ==============================================
class PredictorComprasMejorado:
    def __init__(self, use_log_transform=True):
        self.model = None
        self.feature_scaler = StandardScaler()
        self.target_scaler = StandardScaler()
        self.use_log_transform = use_log_transform
        self.feature_columns = []
        self.is_trained = False

    # ==============================
    # Funciones auxiliares precios
    # ==============================
    def familia(self, nombre):
        """Primeras 3 palabras para detectar familia."""
        return " ".join(nombre.split()[:3]).strip().upper()

    def buscar_producto_similar(self, nombre, lista_nombres, umbral=0.70):
        matches = difflib.get_close_matches(nombre, lista_nombres, n=1, cutoff=umbral)
        return matches[0] if matches else None

    # ==============================
    # Crear dataset mensual
    # ==============================
    def crear_dataset_mensual(self, df_mensual):

        LEAD_TIME = 15
        DIAS_MES = 30
        LT_FACTOR = LEAD_TIME / DIAS_MES   # 0.5
        SS_PCT = 0.20
        TREND = 1.05  # +5%

        df = df_mensual.copy()
        df.columns = [c.lower().strip() for c in df.columns]

        df['canti final']    = pd.to_numeric(df.get('canti final', 0), errors='coerce').fillna(0)
        df['precio entrada'] = pd.to_numeric(df.get('precio entrada', 0), errors='coerce').fillna(0)
        df['precio salida']  = pd.to_numeric(df.get('precio salida', 0), errors='coerce').fillna(0)

        df['tipo_transac'] = df['tipo_transac'].astype(str)
        df['is_saldo_inicial'] = df['tipo_transac'].str.upper() == 'SALDO INICIAL'
        df['is_entrada'] = df['tipo_transac'].str.upper() == 'ENTRADAS'
        df['is_salida']  = df['tipo_transac'].str.upper() == 'SALIDAS'

        df['saldo_inicial_val'] = df['canti final'].where(df['is_saldo_inicial'], 0)
        df['entrada_val'] = df['canti final'].where(df['is_entrada'], 0)
        df['salida_val']  = df['canti final'].where(df['is_salida'], 0).abs()

        df['precio_unit_trans'] = 0.0
        df.loc[df['is_entrada'], 'precio_unit_trans'] = df['precio entrada']
        df.loc[df['is_salida'],  'precio_unit_trans'] = df['precio salida']

        summary = df.groupby(['producto_estado', 'descripcion']).agg(
            saldo_inicial = ('saldo_inicial_val', 'sum'),
            entradas      = ('entrada_val', 'sum'),
            salidas       = ('salida_val', 'sum'),
            precio_unitario = ('precio_unit_trans',
                lambda x: float(x[x>0].mean()) if (x>0).any() else 0.0)
        ).reset_index()

        summary['inventario_real'] = (
            summary['saldo_inicial'] + summary['entradas'] - summary['salidas']
        ).astype(int)

        summary['consumo_enero'] = summary['salidas'].astype(int)
        summary['consumo_febrero'] = (summary['consumo_enero'] * TREND).round().astype(int)
        summary['consumo_marzo']   = (summary['consumo_febrero'] * TREND).round().astype(int)

        summary['demanda_mensual'] = summary['consumo_enero']
        summary['demanda_lead_time'] = (summary['demanda_mensual'] * LT_FACTOR).round().astype(int)
        summary['stock_seguridad'] = (summary['demanda_lead_time'] * SS_PCT).round().astype(int)
        summary['inventario_optimo'] = (summary['demanda_lead_time'] + summary['stock_seguridad']).astype(int)
        summary['diferencia'] = (summary['inventario_real'] - summary['inventario_optimo']).astype(int)

        def estado_from_diff(d):
            if d > 0: return 'SOBRE STOCK'
            if d == 0: return 'OPTIMO'
            return 'QUIEBRE'

        summary['estado'] = summary['diferencia'].apply(estado_from_diff)

        # ======================================================
        # 🔥 VALIDACIÓN DE PRECIO UNITARIO INTELIGENTE (NUEVO)
        # ======================================================
        lista_nombres = summary['descripcion'].tolist()
        summary['precio_unitario'] = summary['precio_unitario'].replace(0, np.nan)

        precio_prom_global = summary['precio_unitario'].mean()

        summary['familia'] = summary['descripcion'].apply(self.familia)

        for idx, row in summary.iterrows():

            precio = row['precio_unitario']
            if not pd.isna(precio) and precio > 0:
                continue

            nombre = row['descripcion']
            fam = row['familia']

            # 1) similitud por nombre
            nombre_similar = self.buscar_producto_similar(nombre, lista_nombres)
            if nombre_similar:
                precio_sim = summary.loc[
                    summary['descripcion'] == nombre_similar, 'precio_unitario'
                ].values[0]

                if not pd.isna(precio_sim) and precio_sim > 0:
                    summary.at[idx, 'precio_unitario'] = precio_sim
                    continue

            # 2) coincidencia por familia
            df_fam = summary[(summary['familia'] == fam) & (summary['precio_unitario'] > 0)]
            if len(df_fam) > 0:
                summary.at[idx, 'precio_unitario'] = df_fam['precio_unitario'].mean()
                continue

            # 3) promedio global
            summary.at[idx, 'precio_unitario'] = precio_prom_global

        summary.drop(columns=['familia'], inplace=True)
        summary['precio_unitario'] = summary['precio_unitario'].astype(float)
        # ======================================================

        cols_order = [
            'producto_estado','descripcion','saldo_inicial','entradas','salidas',
            'inventario_real','precio_unitario',
            'demanda_mensual','demanda_lead_time','stock_seguridad',
            'inventario_optimo','diferencia','estado',
            'consumo_enero','consumo_febrero','consumo_marzo'
        ]
        summary = summary[[c for c in cols_order if c in summary.columns]]

        # ======================================================
        # Construcción df_vertical
        # ======================================================
        rows = []
        for _, r in summary.iterrows():
            producto = r['producto_estado']
            descripcion = r.get('descripcion', '')
            precio = float(r.get('precio_unitario', 0))

            inventario_inicial_mes = int(r.get('saldo_inicial', 0))
            entradas_enero = int(r.get('entradas', 0))
            salidas_enero = int(r.get('salidas', 0))

            cons_ene = int(r['consumo_enero'])
            cons_feb = int(r['consumo_febrero'])
            cons_mar = int(r['consumo_marzo'])

            def calcular_mes(mes, consumo, inicial):
                entradas_mes = 0 if mes != 202401 else entradas_enero
                salidas_mes = consumo
                inv_actual = max(0, inicial + entradas_mes - salidas_mes)

                demanda = consumo
                dlt = int(round(demanda * LT_FACTOR))
                ss = int(round(dlt * SS_PCT))
                inv_opt = dlt + ss
                dif = inv_actual - inv_opt
                est = estado_from_diff(dif)

                return {
                    'producto_estado': producto,
                    'descripcion': descripcion,
                    'mes': mes,
                    'consumo': consumo,
                    'saldo_inicial_mes': inicial,
                    'entradas_mes': entradas_mes,
                    'salidas_mes': salidas_mes,
                    'inventario_actual': inv_actual,
                    'precio_unitario': precio,
                    'demanda_mensual': demanda,
                    'demanda_lead_time': dlt,
                    'stock_seguridad': ss,
                    'inventario_optimo': inv_opt,
                    'diferencia': dif,
                    'estado': est
                }, inv_actual

            row_ene, inventario_inicial_mes = calcular_mes(202401, cons_ene, inventario_inicial_mes)
            row_feb, inventario_inicial_mes = calcular_mes(202402, cons_feb, inventario_inicial_mes)
            row_mar, inventario_inicial_mes = calcular_mes(202403, cons_mar, inventario_inicial_mes)

            rows.extend([row_ene, row_feb, row_mar])

        df_vertical = pd.DataFrame(rows)

        int_cols = ['consumo','saldo_inicial_mes','entradas_mes','salidas_mes',
                    'inventario_actual','demanda_mensual','demanda_lead_time',
                    'stock_seguridad','inventario_optimo','diferencia','mes']

        for c in int_cols:
            df_vertical[c] = df_vertical[c].fillna(0).astype(int)

        return df_vertical



# Inicializar el predictor
predictor = PredictorComprasMejorado()

# Ejecutar la función crear_dataset_mensual()
dataset = pd.read_excel("dataset/00000516-DATA ALM-2.xlsx")
df_mensual_generado = predictor.crear_dataset_mensual(dataset)
df_mensual_generado.to_excel("dataset_mensual_generado.xlsx", index=False)
