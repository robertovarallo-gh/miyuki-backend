from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib import colors as pdf_colors
from collections import namedtuple
from sklearn.cluster import KMeans
import numpy as np
import io
import base64
import math
import stripe
import os
from typing import Tuple
from rgb_palette import RGB_UNIVERSAL_COLORS, ColorInfo as ColorInfoRGB


# Stripe configuration
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
if not STRIPE_SECRET_KEY:
    raise ValueError("STRIPE_SECRET_KEY no configurada")
    
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# Price IDs
STRIPE_PRICE_MONTHLY = 'price_1T2ZcF8hc5PM7463OHDxSErz'
STRIPE_PRICE_YEARLY = 'price_1T2ZcF8hc5PM7463MDrONqhk'

stripe.api_key = STRIPE_SECRET_KEY

import firebase_admin
from firebase_admin import credentials, firestore
import json

# Firebase Admin configuration
if not firebase_admin._apps:
    # En producción (Render), lee del archivo de secret files
    try:
        cred = credentials.Certificate('/etc/secrets/firebase-credentials.json')
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin inicializado desde archivo")
    except FileNotFoundError:
        # En desarrollo local, usa variable de entorno o archivo local
        try:
            firebase_creds = os.environ.get('FIREBASE_CREDENTIALS')
            if firebase_creds:
                cred_dict = json.loads(firebase_creds)
                cred = credentials.Certificate(cred_dict)
            else:
                cred = credentials.Certificate('firebase-credentials.json')
            firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin inicializado localmente")
        except Exception as e:
            print(f"⚠️ Firebase Admin no inicializado: {e}")

db = firestore.client()

app = Flask(__name__)

# Configurar CORS para permitir requests desde Vercel
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://miyuki-frontend.vercel.app",  # Tu dominio de Vercel
            "https://miyuki-frontend-*.vercel.app",  # Preview deploys
            "https://easycuentas.com",
            "https://www.easycuentas.com",
            "https://myeasybeads.com",
            "https://www.myeasybeads.com",
            "http://localhost:3000",  # Para desarrollo local
            "http://127.0.0.1:5000"
        ]
    }
})
 

# ============================================================================
# MIYUKI COLOR PALETTE - Estructura Expandida con Todos los Campos
# ============================================================================
# 301 Colores Reales
# Campos: Español, Inglés, Descripción Oficial Miyuki, URL, RGB
# Fuente: https://nguillers.com/catalog/category/view/s/miyuki-delica/
# ============================================================================

from collections import namedtuple

# Estructura expandida con todos los campos
ColorInfo = namedtuple('ColorInfo', [
    'code',              # Código corto (ej: "1560")
    'name_es',           # Nombre en español
    'name_en',           # Nombre en inglés
    'miyuki_code',       # Código DB completo (ej: "DB1560")
    'miyuki_official',   # Descripción oficial Miyuki Co. Ltd.
    'rgb',               # Tupla RGB (R, G, B)
    'url',                # URL del producto en Nguillers o otros sitios
    'category'  # ← NUEVO CAMPO
])

# Clase wrapper para agregar propiedades calculadas (compatibilidad con código existente)
class ColorInfoWrapper:
    def __init__(self, color_info):
        self._info = color_info
    
    @property
    def code(self):
        return self._info.code
    
    @property
    def name(self):
        """Usa nombre español por defecto para compatibilidad"""
        return self._info.name_es
    
    @property
    def name_es(self):
        return self._info.name_es
    
    @property
    def name_en(self):
        return self._info.name_en
    
    @property
    def miyuki(self):
        """Alias para miyuki_code"""
        return self._info.miyuki_code
    
    @property
    def miyuki_code(self):
        return self._info.miyuki_code
    
    @property
    def miyuki_official(self):
        return self._info.miyuki_official
    
    @property
    def rgb(self):
        return self._info.rgb
    
    @property
    def url(self):
        return self._info.url
    
    @property
    def hex(self):
        """Calcula color hexadecimal"""
        r, g, b = self._info.rgb
        return f"#{r:02x}{g:02x}{b:02x}"

    @property
    def category(self):
        return self._info.category

# ============================================================================
# MIYUKI COLOR PALETTE - 301 Colores Reales de Nguillers Colombia
# Todos los RGB extraídos de fotografías reales de productos
# Fuente: https://nguillers.com/catalog/category/view/s/miyuki-delica/
# ============================================================================

from collections import namedtuple

# Estructura expandida con todos los campos
ColorInfo = namedtuple('ColorInfo', [
    'code',              # Código corto
    'name_es',           # Nombre español
    'name_en',           # Nombre inglés
    'miyuki_code',       # Código DB completo
    'miyuki_official',   # Descripción oficial Miyuki
    'rgb',               # Tupla RGB
    'url',                # URL producto
    'category'  # ← AGREGAR AQUÍ TAMBIÉN
])

# Clase wrapper para compatibilidad con código existente
class ColorInfoWrapper:
    def __init__(self, color_info):
        self._info = color_info
    
    @property
    def code(self):
        return self._info.code
    
    @property
    def name(self):
        """Usa nombre español por defecto para compatibilidad"""
        return self._info.name_es
    
    @property
    def name_es(self):
        return self._info.name_es
    
    @property
    def name_en(self):
        return self._info.name_en
    
    @property
    def miyuki(self):
        """Alias para miyuki_code"""
        return self._info.miyuki_code
    
    @property
    def miyuki_code(self):
        return self._info.miyuki_code
    
    @property
    def miyuki_official(self):
        return self._info.miyuki_official
    
    @property
    def rgb(self):
        return self._info.rgb
    
    @property
    def url(self):
        return self._info.url
    
    @property
    def hex(self):
        """Calcula color hexadecimal"""
        r, g, b = self._info.rgb
        return f"#{r:02x}{g:02x}{b:02x}"

    @property
    def category(self):
        return self._info.category

# COLORES MIYUKI REALES - RGB de fotos de Nguillers Colombia
MIYUKI_COLORS_RAW = {
    (49, 49, 51): ColorInfo("0001", "Gris Metálico Opaco", "Gunmetal", "DB0001", "Gunmetal", (49, 49, 51), "", "metalicos"),
    (35, 51, 76): ColorInfo("0002", "Azul Iris Metálico Oscuro Opaco", "Opaque Metallic Dark Blue Iris", "DB0002", "Opaque Metallic Dark Blue Iris", (35, 51, 76), "", "metalicos"),
    (159, 159, 58): ColorInfo("0003", "Verde Iris Metálico Opaco", "Opaque Metallic Forest Green Iris", "DB0003", "Opaque Metallic Forest Green Iris", (159, 159, 58), "", "metalicos"),
    (50, 25, 75): ColorInfo("0004", "Púrpura Iris Metálico Opaco", "Opaque Metallic Purple Iris", "DB0004", "Opaque Metallic Purple Iris", (50, 25, 75), "", "metalicos"),
    (20, 20, 40): ColorInfo("0005", "Azul Iris Metálico Opaco", "Opaque Metallic Blue Iris", "DB0005", "Opaque Metallic Blue Iris", (20, 20, 40), "", "metalicos"),
    (65, 45, 35): ColorInfo("0006", "Marrón Iris Metálico Opaco", "Opaque Metallic Brown Iris", "DB0006", "Opaque Metallic Brown Iris", (65, 45, 35), "", "metalicos"),
    (130, 70, 45): ColorInfo("0007", "Cobre Iris Metálico", "Opaque Metallic Copper Iris", "DB0007", "Opaque Metallic Copper Iris", (130, 70, 45), "", "metalicos"),
    (0, 0, 0): ColorInfo("0010", "Negro Opaco", "Opaque Black", "DB0010", "Opaque Black", (0, 0, 0), "https://nguillers.com/miyuki-delica-10-0-opaque-black-db0010-1-db0010.html", "negros"),
    (110, 105, 65): ColorInfo("0011", "Verde Oliva metalico", "Metallic Olive", "DB0011", "Metallic Olive", (110, 105, 65), "", "amarillos"),
    (95, 30, 45): ColorInfo("0012", "Rojo Metálico Granate Opaco", "Metallic Garnet Opaque", "DB0012", "Opaque Metallic Garnet", (95, 30, 45), "https://nguillers.com/miyuki-delica-10-0-opaque-metallic-garnet-db0012-1-db0012.html", "metalicos"),
    (160, 160, 165): ColorInfo("0021", "Niquel Plateado", "Nickel Plated", "DB0021", "Nickel Plated", (160, 160, 165), "", "grises"),
    (97, 75, 38): ColorInfo("0022", "Bronce Metálico Opaco", "Metallic Opaque Bronze", "DB0022", "Metallic Bronze", (97, 75, 38), "https://nguillers.com/miyuki-delica-10-0-metallic-bronze-db0022-1-db0022.html", "metalicos"),
    (123, 88, 57): ColorInfo("0022L", "Bronce Metálico Claro", "Metallic Light Bronze", "DB0022L", "Metallic Light Bronze", (123, 88, 57), "", "metalicos"),
    (109, 86, 34): ColorInfo("0023", "Oro Iris Metálico Opaco", "Opaque Metallic Gold Iris", "DB0023", "Opaque Metallic Gold Iris", (109, 86, 34), "", "metalicos"),
    (92, 101, 84): ColorInfo("0024", "Verde oliva metálico con brillo tornasolado", "Opaque Metallic Olive Green Iris", "DB0024", "Opaque Metallic Olive Green Iris", (92, 101, 84), "", "metalicos"),
    (21, 53, 74): ColorInfo("0025", "Azul Iris Metálico Opaco", "Opaque Metallic Blue Iris", "DB0025", "Opaque Metallic Blue Iris", (21, 53, 74), "", "metalicos"),
    (40, 45, 50): ColorInfo("0026", "Acero Iris Metálico Opaco", "Opaque Metallic Steel Iris", "DB0026", "Opaque Metallic Steel Iris", (40, 45, 50), "", "metalicos"),
    (40, 75, 70): ColorInfo("0027", "Verde Azulado Iris Metálico", "Metallic Dark Green Iris", "DB0027", "Metallic Dark Green Iris", (40, 75, 70), "", "metalicos"),
    (105, 100, 50): ColorInfo("0029", "Oliva Dorado Iris Metálico Opaco", "Opaque Metallic Golden Olive Iris", "DB0029", "Opaque Metallic Golden Olive Iris", (105, 100, 50), "", "metalicos"),
    (232, 200, 15): ColorInfo("0031", "Dorado bañado en oro de 24 quilates", "24kt Gold Plated", "DB0031", "24kt Gold Plated", (232, 200, 15), "", "amarillos"),
    (222, 184, 68): ColorInfo("0031L", "Bronce claro metálico estándar", "Metallic Light Bronze Iris.", "DB0031L", "Metallic Light Bronze Iris.", (222, 184, 68), "", "metalicos"),
    (245, 182, 71): ColorInfo("0033", "Cristal Forrado en Oro de 24 Quilates", "24kt Gold Lined Crystal", "DB0033", "24kt Gold Lined Crystal", (245, 182, 71), "", "naranjas"),
    (255, 223, 100): ColorInfo("0034", "Oro Claro Bañado en 24 Quilates", "24kt Light Gold Plated", "DB0034", "24kt Light Gold Plated", (255, 223, 100), "", "amarillos"),
    (160, 156, 132): ColorInfo("0035", "Plateado galvanizado metálico", "Galvanized Silver Metallic", "DB0035", "Galvanized Silver Metallic", (160, 156, 132), "", "metalicos"),
    (126, 91, 85): ColorInfo("0037", "Cobre Línea Cristal", "Crystal Copper Line", "DB0037", "Copper Lined Crystal", (126, 91, 85), "https://nguillers.com/miyuki-delica-10-0-copper-lined-crystal-db0037-1-db0037.html", "rojos"),
    (175, 180, 185): ColorInfo("0038", "Plateado Paladio", "Palladium Plated", "DB0038", "Palladium Plated", (175, 180, 185), "", "grises"),
    (178, 108, 82): ColorInfo("0040", "Cobre Metálico Opaco", "Metallic Opaque Copper", "DB0040", "Metallic Opaque Copper", (178, 108, 82), "https://nguillers.com/miyuki-delica-10-0-metallic-opaque-copper-db0040-1-db0040.html", "metalicos"),
    (183, 185, 177): ColorInfo("0041", "Plateado Transparente Línea Plateada", "Silver Transparent Silver Line", "DB0041", "Silver Lined Crystal", (183, 185, 177), "https://nguillers.com/miyuki-delica-10-0-silver-lined-crystal-db0041-1-db0041.html", "transparentes"),
    (217, 180, 79): ColorInfo("0042", "Dorado Línea Plateada", "Gold Silver Line", "DB0042", "Silver Lined Gold", (217, 180, 79), "https://nguillers.com/miyuki-delica-10-0-silver-lined-gold-db0042-1-db0042.html", "naranjas"),
    (172, 30, 7): ColorInfo("0043", "Rojo Naranja Forrado en Plata Transparente", "Transparent Silver Lined Red-Orange", "DB0043", "Transparent Silver Lined Red-Orange", (172, 30, 7), "https://nguillers.com/miyuki-delica-10-0-silver-lined-padparadscha-db0043-1-db0043.html", "transparentes"),
    (100, 180, 205): ColorInfo("0044", "Azul Aguamarina Forrado en Plata", "Silver Lined Aquamarine", "DB044", "Silver Lined Aquamarine", (100, 180, 205), "", "azules"),
    (214, 112, 29): ColorInfo("0045", "Naranja Forrado en Plata Transparente", "Transparent Silver Lined Orange", "DB0045", "Transparent Silver Lined Orange", (214, 112, 29), "", "transparentes"),
    (30, 118, 50): ColorInfo("0046", "Verde Forrado en Plata", "Transparent Silver Lined Light Green", "DB0046", "Transparent Silver Lined Light Green", (30, 118, 50), "", "verdes"),
    (0, 50, 160): ColorInfo("0047", "Azul Transparente Línea Plateada", "Transparent Silver Line Blue", "DB0047", "Silver Lined Sapphire", (0, 50, 160), "https://nguillers.com/miyuki-delica-10-0-silver-lined-sapphire-db0047-1-db0047.html", "transparentes"),
    (140, 140, 140): ColorInfo("0048", "Plata Oscuro Transparente Línea Plateada", "Transparent Silver Line Dark Silver", "DB0048", "Silver Lined Dark Gray", (140, 140, 140), "https://nguillers.com/miyuki-delica-10-0-silver-lined-dark-gray-db0048-1-db0048.html", "transparentes"),
    (250, 250, 249): ColorInfo("0050", "Blanco Brillante", "Crystal Luster", "DB0050", "Crystal Luster", (250, 250, 249), "", "blancos"),
    (245, 242, 239): ColorInfo("0051", "Aurora Boreal Transparente", "Crystal AB", "DB0051", "Crystal AB", (245, 242, 239), "https://nguillers.com/miyuki-delica-10-0-crystal-ab-db0051-1-db0051.html", "transparentes"),
    (253, 245, 236): ColorInfo("0052", "Melocotón muy Pálido Forrado con Aurora Boreal.", "Lined Palest Peach AB", "DB0052", "Lined Palest Peach AB", (253, 245, 236), "", "blancos"),
    (244, 241, 179): ColorInfo("0053", "Amarillo Pálido Transparente AB.", "Transparent Pale Yellow AB", "DB0053", "Transparent Pale Yellow AB", (244, 241, 179), "", "transparentes"),
    (199, 138, 115): ColorInfo("0054", "Melocoton Oscuro", "Lined Peach AB", "DB0054", "Lined Peach AB", (199, 138, 115), "", "naranjas"),
    (244, 217, 222): ColorInfo("0055", "Rosa Cristal Forrado con Aurora Boreal", "Crystal Rose AB Lined", "DB0055", "Crystal Rose AB Lined", (244, 217, 222), "", "rojos"),
    (128, 60, 134): ColorInfo("0056", "Magenta AB Línea Color", "Color Lined Magenta AB", "DB0056", "Color Lined Magenta AB", (128, 60, 134), "https://nguillers.com/miyuki-delica-10-0-color-lined-magenta-ab-db0056-1-db0056.html", "morados"),
    (135, 199, 226): ColorInfo("0057", "Azul Cielo", "Aqua Lined Crystal AB", "DB0057", "Aqua Lined Crystal AB", (135, 199, 226), "", "azules"),
    (81, 130, 153): ColorInfo("0058", "Azul Marino", "Marine Blue Lined Crystal AB", "DB0058", "Marine Blue Lined Crystal AB", (81, 130, 153), "", "azules"),
    (112, 108, 127): ColorInfo("0059", "Amatista Forrado con Brillo Iridiscente", "Amethyst Lined Crystal AB", "DB0059", "Amethyst Lined Crystal AB", (112, 108, 127), "", "azules"),
    (94, 132, 129): ColorInfo("0060", "Verde Lima", "Lime Lined Crystal AB", "DB0060", "Lime Lined Crystal AB", (94, 132, 129), "", "azules"),
    (88, 66, 86): ColorInfo("0061", "Topacio claro", "Purple Lined Light Topaz Luster", "DB0061", "Purple Lined Light Topaz Luster", (88, 66, 86), "", "morados"),
    (162, 52, 67): ColorInfo("0062", "Arándano claro forrado con topacio brillante", "Light Cranberry Lined Topaz Luster", "DB0062", "Light Cranberry Lined Topaz Luster", (162, 52, 67), "", "rojos"),
    (66, 111, 244): ColorInfo("0063", "Azul cobalto", "Cobalt Lined Sapphire AB", "DB0063", "Cobalt Lined Sapphire AB", (66, 111, 244), "", "azules"),
    (84, 49, 37): ColorInfo("0064", "Marrón grisáceo suave", "Taupe Lined Crystal AB", "DB0064", "Taupe Lined Crystal AB", (84, 49, 37), "", "naranjas"),
    (161, 102, 18): ColorInfo("0065", "Topacio forrado AB", "Lined Topaz AB", "DB0065", "Lined Topaz AB", (161, 102, 18), "", "naranjas"),
    (244, 242, 242): ColorInfo("0666", "Blanco Forrado Cristal AB", "White Lined Crystal AB", "DB0666", "White Lined Crystal AB", (244, 242, 242), "", "blancos"),
    (234, 169, 139): ColorInfo("0067", "Melocotón Claro con Brillo Interior", "Light Peach Lined Crystal Luster", "DB0067", "Light Peach Lined Crystal Luster", (234, 169, 139), "", "naranjas"),
    (247, 177, 152): ColorInfo("0068", "Melocotón Transparente Forrado Brillante", "Peach Lined Crystal Luster", "DB0068", "Peach Lined Crystal Luster", (247, 177, 152), "", "transparentes"),
    (185, 142, 124): ColorInfo("0069", "rosa pálido forrado con cristal AB", "Blush Lined Crystal AB", "DB0069", "Blush Lined Crystal AB", (185, 142, 124), "", "naranjas"),
    (228, 121, 129): ColorInfo("0070", "rosa coral con forro de cristal brillante", "Coral Lined Crystal Luster", "DB0070", "Coral Lined Crystal Luster", (228, 121, 129), "", "rojos"),
    (255, 223, 232): ColorInfo("0071", "Rosa Transparente AB", "Transparent Pink AB", "DB0071", "Transparent Pink AB", (255, 223, 232), "", "transparentes"),
    (181, 123, 155): ColorInfo("0072", "Lila Pálido Forrado AB", "Lined Pale Lilac AB", "DB0072", "Lined Pale Lilac AB", (181, 123, 155), "", "rosas"),
    (137, 57, 127): ColorInfo("0073", "Lila Forrado Transparente AB", "Transparent Color Lined Lilac AB", "DB0073", "Transparent Color Lined Lilac AB", (137, 57, 127), "", "transparentes"),
    (136, 38, 95): ColorInfo("0074", "Fucsia Transparente Lined AB.", "Fuchsia Lined Crystal AB", "DB0074", "Fuchsia Lined Crystal AB", (136, 38, 95), "", "transparentes"),
    (185, 55, 74): ColorInfo("0075", "Rosado Oscuro Forrado AB", "Dark Rose AB Lined-Dyed.", "DB0075", "Dark Rose AB Lined-Dyed.", (185, 55, 74), "", "rojos"),
    (85, 126, 195): ColorInfo("0076", "Azul Claro Forrado de Cristal AB", "Light Blue Lined Crystal AB", "DB0076", "Light Blue Lined Crystal AB", (85, 126, 195), "", "azules"),
    (61, 92, 184): ColorInfo("0077", "Azul Forrado de Cristal AB", "Transparente Color Forrado Azul AB", "DB0077", "Transparente Color Forrado Azul AB", (61, 92, 184), "", "azules"),
    (173, 216, 230): ColorInfo("0078", "Azul Aguamarina", "Aquamarine Blue", "DB0078", "Transparent Aqua", (173, 216, 230), "https://nguillers.com/miyuki-delica-10-0-transparent-aqua-db0078-1-db0078.html", "azules"),
    (102, 167, 171): ColorInfo("0079", "Azul Agua Cristal ForradoAB", "Aqua Blue Lined Crystal AB", "DB0079", "Aqua Blue Lined Crystal AB", (102, 167, 171), "", "azules"),
    (193, 172, 197): ColorInfo("0080", "Violeta Pálido Forrado de Cristal Lustre", "Pale Violet Lined Crystal Luster", "DB0080", "Pale Violet Lined Crystal Luster", (193, 172, 197), "", "morados"),
    (92, 97, 101): ColorInfo("0081", "Gris Oscuro Forrado de Cristal AB", "Gray Lined Crystal AB", "DB0081", "Gray Lined Crystal AB", (92, 97, 101), "", "grises"),
    (208, 184, 186): ColorInfo("0082", "Rosa pálido transparente AB", "Transparent Pale Pink AB", "DB0082", "Transparent Pale Pink AB", (208, 184, 186), "", "transparentes"),
    (162, 210, 216): ColorInfo("0083", "Aguamarina Pálido Transparente AB", "Transparent Pale Aqua AB", "DB0083", "Transparent Pale Aqua AB", (162, 210, 216), "", "transparentes"),
    (107, 144, 138): ColorInfo("0084", "Aguamarina Forrado Cristal AB", "Sea Foam Lined Crystal", "DB0084", "Sea Foam Lined Crystal", (107, 144, 138), "", "azules"),
    (48, 69, 109): ColorInfo("0085", "Azul Forrado Aguamarina AB", "Blue Lined Aqua AB", "DB0085", "Blue Lined Aqua AB", (48, 69, 109), "", "azules"),
    (29, 43, 61): ColorInfo("0086", "Azul Oscuro Forrado de Cristal AB", "Noir Lined Crystal AB", "DB0086", "Noir Lined Crystal AB", (29, 43, 61), "", "azules"),
    (102, 59, 32): ColorInfo("0087", "Ámbar Forrado de Topacio Claro AB.", "Root Beer Lined Light Topaz AB", "DB0087", "Root Beer Lined Light Topaz AB", (102, 59, 32), "", "marrones"),
    (145, 83, 70): ColorInfo("0088", "Topacio Claro Forrado Baya AB", "Berry Lined Light Topaz AB", "DB0088", "Berry Lined Light Topaz AB", (145, 83, 70), "", "rojos"),
    (95, 90, 69): ColorInfo("0089", "Azul Forrado de Topacio Claro AB", "Blue Lined Light Topaz AB", "DB0089", "Blue Lined Light Topaz AB", (95, 90, 69), "", "marrones"),
    (106, 73, 42): ColorInfo("0091", "Arándano Forrado de Topacio Claro AB", "Cranberry Lined Light Topaz AB", "DB0091", "Cranberry Lined Light Topaz AB", (106, 73, 42), "", "marrones"),
    (209, 75, 83): ColorInfo("0098", "Siam Lustre Transparente Claro", "Transparent Light Siam Luster", "DB0098", "Transparent Light Siam Luster", (209, 75, 83), "", "transparentes"),
    (229, 163, 119): ColorInfo("0099", "Topacio Lustre Claro Transparente", "Transparent Light Topaz Luster", "DB0099", "Transparent Light Topaz Luster", (229, 163, 119), "", "transparentes"),
    (214, 140, 75): ColorInfo("0100", "Topacio Claro Transparente AB", "Transparent Light Topaz AB", "DB0100", "", (214, 140, 75), "", "transparentes"),
    (203, 163, 95): ColorInfo("0101", "Topacio Ahumado Lustre Glaseado Claro Transparente", "Transparent Light Smoky Topaz Glazed Luster", "DB0101", "Transparent Light Smoky Topaz Glazed Luster", (203, 163, 95), "", "transparentes"),
    (146, 79, 56): ColorInfo("0102", "Topacio Melocotón Lustre Dorado Transparente", "Transparent Peach Topaz Gold Luster", "DB102", "Transparent Peach Topaz Gold Luster", (146, 79, 56), "", "transparentes"),
    (64, 30, 26): ColorInfo("0103", "Rojo Lustre Dorado", "Gold Red Luster", "DB103", "Gold Red Luster", (64, 30, 26), "", "rojos"),
    (87, 63, 77): ColorInfo("0104", "Frambuesa Tornasolado Lustre Dorado", "Claret Rainbow Gold Luster", "DB104", "Claret Rainbow Gold Luster", (87, 63, 77), "", "rosas"),
    (80, 7, 15): ColorInfo("0105", "Rojo Transparente con Lustre Dorado", "Transparent Red Gold Luster", "DB0105", "Transparent Red Gold Luster", (80, 7, 15), "", "transparentes"),
    (216, 147, 118): ColorInfo("0106", "Rosa Concha Lustre Glaseado Transparente", "ransparent Shell Pink Glazed Luster", "DB0106", "ransparent Shell Pink Glazed Luster", (216, 147, 118), "", "transparentes"),
    (165, 163, 170): ColorInfo("0107", "Gris Tornasolado Dorado Transparente Brillante", "Transparent Gray Rainbow Gold Luster", "DB0107", "Transparent Gray Rainbow Gold Luster", (165, 163, 170), "", "transparentes"),
    (116, 66, 74): ColorInfo("0108", "Amatista Dorado Brillante", "Amethyst Gold Luster", "DB0108", "Amethyst Gold Luster", (116, 66, 74), "", "rojos"),
    (222, 219, 207): ColorInfo("0109", "Marfil Cristal Dorado Transparente Brillante", "Transparent Crystal Ivory Gold Luster", "DB0109", "Transparent Crystal Ivory Gold Luster", (222, 219, 207), "", "transparentes"),
    (158, 175, 185): ColorInfo("0110", "Azul Marino Claro Dorado Transparente Brillante", "ransparent Light Marine Blue Gold Luster", "DB0110", "ransparent Light Marine Blue Gold Luster", (158, 175, 185), "", "transparentes"),
    (80, 82, 89): ColorInfo("0111", "Azul Grisáceo Tornasolado Dorado Transparente Brillante", "Transparent Blue Gray Rainbow Gold Luster", "DB0111", "Transparent Blue Gray Rainbow Gold Luster", (80, 82, 89), "", "transparentes"),
    (60, 101, 101): ColorInfo("0112", "Espuma de Mar Transparente Brillante", "Transparent Sea Foam Luster", "DB0112", "Transparent Sea Foam Luster", (60, 101, 101), "", "transparentes"),
    (89, 162, 217): ColorInfo("0113", "Azul Transparente Brillante", "Transparent Blue Luster", "DB0113", "Transparent Blue Luster", (89, 162, 217), "", "transparentes"),
    (184, 185, 177): ColorInfo("0114", "Gris Plata Dorado Transparente Brillante", "Transparent Silver Gray Gold Luster", "DB0114", "Transparent Silver Gray Gold Luster", (184, 185, 177), "", "transparentes"),
    (173, 137, 94): ColorInfo("0115", "Topacio Oscuro Dorado Brillante", "Dark Topaz Gold Luster", "DB0115", "Dark Topaz Gold Luster", (173, 137, 94), "", "naranjas"),
    (111, 40, 32): ColorInfo("0116", "Rojo Metálico Transparente Brillante", "Transparent Red Metallic Luster", "DB0116", "Transparent Red Metallic Luster", (111, 40, 32), "", "metalicos"),
    (111, 77, 104): ColorInfo("0117", "Violeta Dorado Brillante", "Violet Gold Luster", "DB0117", "Violet Gold Luster", (111, 77, 104), "", "rosas"),
    (152, 97, 44): ColorInfo("0118", "Azafrán Transparente Brillante", "Transparent Saffron Luster", "DB0118", "Transparent Saffron Luster", (152, 97, 44), "", "transparentes"),
    (144, 84, 45): ColorInfo("0119", "Miel Transparente Brillante", "Transparent Honey Luster", "DB0119", "Transparent Honey Luster", (144, 84, 45), "", "transparentes"),
    (169, 71, 66): ColorInfo("0120", "Vino Tinto Topacio Oscuro", "Dark Topaz Claret Luster", "DB0120", "Dark Topaz Claret Luster", (169, 71, 66), "", "rojos"),
    (115, 76, 46): ColorInfo("0121", "Topacio Albaricoque Dorado Transparente Brillante", "Transparent Apricot Topaz Gold Luster", "DB0121", "Transparent Apricot Topaz Gold Luster", (115, 76, 46), "", "transparentes"),
    (148, 161, 141): ColorInfo("0122", "Topacio Dorado Transparente Brillante", "Topaz Transparent Gold Luster", "DB0122", "Topaz Transparent Gold Luster", (148, 161, 141), "", "transparentes"),
    (82, 67, 52): ColorInfo("0123", "Oliva Ahumado Transparente Brillante", "Transparent Smoky Olive Luster", "DB0123", "Transparent Smoky Olive Luster", (82, 67, 52), "", "transparentes"),
    (169, 156, 89): ColorInfo("0124", "Oliva Dorado Transparente Brillante", "Transparent Golden Olive Luster", "DB0124", "Transparent Golden Olive Luster", (169, 156, 89), "", "transparentes"),
    (35, 81, 71): ColorInfo("0125", "Esmeralda Dorado Brillante", "Emerald Gold Luster", "DB0125", "Emerald Gold Luster", (35, 81, 71), "", "azules"),
    (101, 78, 75): ColorInfo("0126", "Canela Tornasolado Dorado Brillante", "Cinnamon Rainbow Gold Luster", "DB0126", "Cinnamon Rainbow Gold Luster", (101, 78, 75), "", "rojos"),
    (58, 66, 65): ColorInfo("0127", "Verde Bosque Tornasolado Dorado Brillante", "Forest Green Rainbow Gold Luster", "DB0127", "Forest Green Rainbow Gold Luster", (58, 66, 65), "", "azules"),
    (72, 54, 65): ColorInfo("0128", "Ciruela Dorado Brillante", "Plum Gold Luster", "DB0128", "Plum Gold Luster", (72, 54, 65), "", "rosas"),
    (99, 60, 73): ColorInfo("0129", "Mora Tornasolado Dorado Brillante", "Mulberry Rainbow Gold Luster", "DB0129", "Mulberry Rainbow Gold Luster", (99, 60, 73), "", "rosas"),
    (66, 76, 47): ColorInfo("0131", "Oliva Oscuro Tornasolado Opaco Brillante", "Opaque Dark Olive Luster AB", "DB0131", "Opaque Dark Olive Luster AB", (66, 76, 47), "", "verdes"),
    (89, 100, 118): ColorInfo("0132", "Gris Azulado Opaco Brillante", "Opaque Blue Gray Luster", "DB0132", "Opaque Blue Gray Luster", (89, 100, 118), "", "azules"),
    (126, 113, 56): ColorInfo("0133", "Oliva Dorado Opaco Brillante", "Opaque Golden Olive Luster AB", "DB0133", "Opaque Golden Olive Luster AB", (126, 113, 56), "", "marrones"),
    (61, 67, 85): ColorInfo("0134", "Gris Púrpura Tornasolado Opaco Brillante", "Opaque Purple Gray Rainbow Luster", "DB0134", "Opaque Purple Gray Rainbow Luster", (61, 67, 85), "", "azules"),
    (72, 67, 113): ColorInfo("0135", "Berenjena Dorado Opaco Brillante AB", "Opaque Eggplant Gold Luster AB", "DB0135", "Opaque Eggplant Gold Luster AB", (72, 67, 113), "", "azules"),
    (76, 177, 176): ColorInfo("0136", "Ópalo Marino Opaco", "Opaque Sea Opal", "DB0136", "Opaque Sea Opal", (76, 177, 176), "", "azules"),
    (241, 241, 242): ColorInfo("0141", "Cristal Transparente", "Transparent Crystal", "DB0141", "Transparent Crystal", (241, 241, 242), "", "transparentes"),
    (141, 92, 19): ColorInfo("0144", "Bronce transparente", "Transparent Silver Line Bronze", "DB0144", "Silver Lined Bronze", (141, 92, 19), "https://nguillers.com/miyuki-delica-10-0-silver-lined-bronze-db0144-1-db0144.html", "transparentes"),
    (210, 192, 69): ColorInfo("0145", "Amarillo Forrado en Plata", "Silver Lined Yellow", "DB0145", "Silver Lined Yellow", (210, 192, 69), "", "amarillos"),
    (138, 109, 115): ColorInfo("0146", "Lila Forrado en Plata", "Silver Lined Lilac", "DB0146", "Silver Lined Lilac", (138, 109, 115), "", "rojos"),
    (163, 167, 81): ColorInfo("0147", "Amarillo Limón Forrado en Plata", "Silver Lined Lime Yellow", "DB0147", "Silver Lined Lime Yellow", (163, 167, 81), "", "amarillos"),
    (2, 59, 22): ColorInfo("0148", "Verde Oscuro Forrado en Plata", "Silver Lined Dark Green", "DB0148", "Silver Lined Dark Green", (2, 59, 22), "", "verdes"),
    (96, 184, 213): ColorInfo("0149", "Azul Transparente Línea Plateada", "Transparent Silver Line Blue", "DB0149", "Silver Lined Capri Blue", (96, 184, 213), "https://nguillers.com/miyuki-delica-10-0-silver-lined-capri-blue-db0149-1-db0149.html", "transparentes"),
    (173, 109, 83): ColorInfo("0150", "Chocolate Transparente Línea Plateada", "Transparent Silver Line Chocolate", "DB0150", "Silver Lined Chocolate", (173, 109, 83), "https://nguillers.com/miyuki-delica-10-0-silver-lined-chocolate-db0150-1-db0150.html", "transparentes"),
    (241, 94, 0): ColorInfo("0151", "Naranja Transparente AB", "Transparent Orange AB", "DB0151", "Transparent Orange AB", (241, 94, 0), "", "transparentes"),
    (65, 106, 76): ColorInfo("0152", "Verde Transparente AB", "Transparent Green AB", "DB0152", "Transparent Green AB", (65, 106, 76), "", "transparentes"),
    (255, 248, 231): ColorInfo("0157", "Crema Opaco AB", "Opaque Cream AB", "DB0157", "Opaque Cream AB", (255, 248, 231), "", "blancos"),
    (178, 151, 161): ColorInfo("0158", "Lila Opaco AB", "Opaque Lilac AB", "DB0158", "Opaque Lilac AB", (178, 151, 161), "", "rosas"),
    (237, 59, 56): ColorInfo("0159", "Rojo Bermellón Opaco AB", "Opaque Vermillion Red AB", "DB0159", "Opaque Vermillion Red AB", (237, 59, 56), "", "rojos"),
    (239, 220, 15): ColorInfo("0160", "Amarillo Opaco AB", "Opaque Yellow AB", "DB0160", "Opaque Yellow AB", (239, 220, 15), "", "amarillos"),
    (252, 93, 55): ColorInfo("0161", "Naranja Opaco AB", "Opaque Orange AB", "DB0161", "Opaque Orange AB", (252, 93, 55), "", "rojos"),
    (177, 52, 63): ColorInfo("0162", "Rojo Opaco AB", "Opaque Red AB", "DB0162", "Opaque Red AB", (177, 52, 63), "", "rojos"),
    (68, 130, 67): ColorInfo("0163", "Verde Opaco AB", "Opaque Green AB", "DB0163", "Opaque Green AB", (68, 130, 67), "", "verdes"),
    (180, 231, 246): ColorInfo("0164", "Azul Opaco AB", "Blue Opaque AB", "DB0164", "Opaque Blue AB", (180, 231, 246), "https://nguillers.com/miyuki-delica-seed-bead-round-n-11-opaque-blue-ab-db0164-db0164.html", "azules"),
    (42, 52, 140): ColorInfo("0165", "Azul Cobalto Opaco AB", "Opaque Cobalt AB", "DB0165", "Opaque Cobalt AB", (42, 52, 140), "", "azules"),
    (104, 178, 184): ColorInfo("0166", "Verde Turquesa Opaco AB", "Opaque Turquoise Green AB", "DB0166", "Opaque Turquoise Green AB", (104, 178, 184), "", "azules"),
    (109, 128, 217): ColorInfo("0167", "Azul Medio Opaco AB", "Opaque Medium Blue AB", "DB0167", "Opaque Medium Blue AB", (109, 128, 217), "", "azules"),
    (123, 122, 131): ColorInfo("0168", "Gris Opaco AB", "Opaque Gray AB", "DB0168", "Opaque Gray AB", (123, 122, 131), "", "grises"),
    (169, 189, 91): ColorInfo("0169", "Verde Opaco AB", "Green Opaque AB", "DB0169", "Opaque Green AB", (169, 189, 91), "https://nguillers.com/miyuki-delica-seed-bead-round-n-11-opaque-green-ab-db0169-db0169.html", "verdes"),
    (104, 65, 60): ColorInfo("0170", "Topacio Transparente AB", "Transparent Topaz AB", "DB0170", "Transparent Topaz AB", (104, 65, 60), "", "transparentes"),
    (240, 202, 65): ColorInfo("0171", "Amarillo Transparente AB", "Transparent Yellow AB", "DB0171", "Transparent Yellow AB", (240, 202, 65), "", "transparentes"),
    (188, 6, 60): ColorInfo("0172", "Rojo Transparente AB", "Transparent Red AB", "DB0172", "Transparent Red AB", (188, 6, 60), "", "transparentes"),
    (107, 84, 96): ColorInfo("0173", "Lila Transparente AB", "Transparent Lilac AB", "DB0173", "Transparent Lilac AB", (107, 84, 96), "", "transparentes"),
    (166, 192, 78): ColorInfo("0174", "Verde amarillento Brillante AB", "Transparent Chartreuse AB", "DB0174", "Transparent Chartreuse AB", (166, 192, 78), "", "verdes"),
    (42, 158, 108): ColorInfo("0175", "Verde Oscuro Transparente AB", "Transparent Dark Green AB", "DB0175", "Transparent Dark Green AB", (42, 158, 108), "", "transparentes"),
    (177, 229, 245): ColorInfo("0176", "Azul Oscuro Transparente AB", "Transparent Dark Blue AB", "DB0176", "Transparent Dark Blue AB", (177, 229, 245), "", "transparentes"),
    (63, 101, 168): ColorInfo("0177", "Azul Capri Transparente AB", "Transparent Capri Blue AB", "DB0177", "Transparent Capri Blue AB", (63, 101, 168), "", "transparentes"),
    (50, 56, 141): ColorInfo("0178", "Cobalto Transparente AB", "Transparent Cobalt AB", "DB0178", "Transparent Cobalt AB", (50, 56, 141), "", "transparentes"),
    (88, 101, 112): ColorInfo("0179", "Gris Transparente AB", "Transparent Gray AB", "DB0179", "Transparent Gray AB", (88, 101, 112), "", "transparentes"),
    (254, 254, 254): ColorInfo("200", "Blanco Opaco Tiza", "Opaque Chalk White", "DB200", "Opaque Chalk White", (254, 254, 254), "", "blancos"),
    (245, 241, 240): ColorInfo("0201", "Blanco Opaco Brillante", "Opaque White Luster", "DB0201", "Opaque White Luster", (245, 241, 240), "https://nguillers.com/miyuki-delica-10-0-opaque-white-luster-db0201-1-db0201.html", "blancos"),
    (255, 254, 255): ColorInfo("0202", "Blanco Perla Opaco AB", "Opaque Pearl White AB", "DB0202", "Opaque Pearl White AB", (255, 254, 255), "", "blancos"),
    (229, 222, 204): ColorInfo("0203", "Blanco Opaco Esmaltado Brillante", "White Opaque Luster Glazed", "DB0203", "Opaque White Glazed Luster", (229, 222, 204), "https://nguillers.com/miyuki-delica-n-11opaque-white-glazed-luster-db0203-db0203.html", "naranjas"),
    (254, 241, 219): ColorInfo("0204", "Beige Glaseado Claro Opaco Brillante", "Opaque Light Beige Glazed Luster", "DB0204", "Opaque Light Beige Glazed Luster", (254, 241, 219), "", "naranjas"),
    (241, 229, 198): ColorInfo("0205", "Ceilán Beige", "Ceylon Beige", "DB0205", "Ceylon Beige", (241, 229, 198), "", "naranjas"),
    (238, 215, 198): ColorInfo("0206", "Rosado Opaco Glaseado", "Opaque Pink Glazed", "DB0206", "Opaque Bisque White Luster", (238, 215, 198), "https://nguillers.com/miyuki-delica-10-0-opaque-bisque-white-luster-db0206-1-db0206.html", "naranjas"),
    (242, 169, 159): ColorInfo("0207", "Melocotón Opaco Brillante", "Opaque Peach Luster", "DB0207", "Opaque Peach Luster", (242, 169, 159), "", "rojos"),
    (221, 181, 156): ColorInfo("0208", "Tostado Opaco Brillante", "Opaque Tan Luster", "DB0208", "Opaque Tan Luster", (221, 181, 156), "", "naranjas"),
    (219, 222, 229): ColorInfo("0209", "Gris Claro Opaco Brillante", "Opaque Light Gray Luster", "DB0209", "Opaque Light Gray Luster", (219, 222, 229), "", "blancos"),
    (193, 149, 160): ColorInfo("0210", "Rosado Glaseado Opaco Brillante", "Opaque Pink Glazed Luster", "DB0210", "Opaque Pink Luster", (193, 149, 160), "https://nguillers.com/miyuki-delica-10-0-opaque-pink-luster-db0210-1-db0210.html", "rojos"),
    (249, 243, 238): ColorInfo("0211", "Alabastro Glaseado Opaco Brillante", "Opaque Alabaster Glazed Luster", "DB0211", "Opaque Alabaster Glazed Luster", (249, 243, 238), "", "blancos"),
    (170, 11, 26): ColorInfo("0214", "Rojo Opaco Brillante", "Opaque Red Luster", "DB0214", "Opaque Red Luster", (170, 11, 26), "", "rojos"),
    (139, 196, 245): ColorInfo("0215", "Azul Cielo Opaco Brillante", "Opaque Sky Blue Luste", "DB0215", "Opaque Sky Blue Luste", (139, 196, 245), "", "azules"),
    (30, 44, 150): ColorInfo("0216", "Azul Real Opaco Brillante", "Opaque Royal Blue Luster", "DB0216", "Opaque Royal Blue Luster", (30, 44, 150), "", "azules"),
    (97, 192, 200): ColorInfo("0217", "Verde Azulado Opaco Brillante AB", "Opaque Teal Luster AB", "DB0217", "Opaque Teal Luster AB", (97, 192, 200), "", "azules"),
    (129, 212, 236): ColorInfo("0218", "Azul Turquesa Medio Opaco Brillante", "Opaque Medium Turquoise Blue Luster", "DB0218", "Opaque Medium Turquoise Blue Luster", (129, 212, 236), "", "azules"),
    (251, 251, 251): ColorInfo("0220", "Ópalo Blanco", "White Opa", "DB0220", "White Opa", (251, 251, 251), "", "blancos"),
    (253, 253, 250): ColorInfo("0221", "Ópalo Blanco Forrado en Oro", "White Opal Gilt Lined", "DB0221", "White Opal Gilt Lined", (253, 253, 250), "", "blancos"),
    (249, 250, 248): ColorInfo("0222", "Ópalo Blanco AB", "White Opal AB", "DB0222", "White Opal AB", (249, 250, 248), "", "blancos"),
    (254, 252, 244): ColorInfo("0223", "Ópalo Forrado en Plata AB", "Opal Silver Lined Rainbow", "DB0223", "Opal Silver Lined Rainbow", (254, 252, 244), "", "blancos"),
    (255, 228, 185): ColorInfo("0230", "Ópalo Forrado en Oro de 24 quilates", "24kt Gold Lined Opal", "DB0230", "24kt Gold Lined Opal", (255, 228, 185), "", "naranjas"),
    (255, 255, 255): ColorInfo("0231", "Blanco Cristal Forrado", "Lined Crystal White", "DB0231", "Lined Crystal White", (255, 255, 255), "", "blancos"),
    (253, 242, 177): ColorInfo("0232", "Amarillo Pálido Ceilán Brillante", "Ceylon Pale Yellow Luster", "DB0232", "Ceylon Pale Yellow Luster", (253, 242, 177), "", "amarillos"),
    (254, 221, 135): ColorInfo("0233", "Amarillo Cristal Forrado Brillante", "Lined Crystal Yellow Luster", "DB0233", "Lined Crystal Yellow Luster", (254, 221, 135), "", "naranjas"),
    (251, 240, 236): ColorInfo("0234", "Rosa Pálido Ceilán", "Ceylon Pale Pink", "DB0234", "Ceylon Pale Pink", (251, 240, 236), "", "blancos"),
    (13, 98, 82): ColorInfo("0235", "Salmon Ceilán", "Ceylon Salmon", "DB0235", "Ceylon Salmon", (13, 98, 82), "https://nguillers.com/miyuki-delica-10-0-ceylon-salmon-db0235-1-db0235.html", "rojos"),
    (233, 85, 123): ColorInfo("0236", "Rosa Clavel Ceilán", "Ceylon Carnation Pink", "DB0236", "Ceylon Carnation Pink", (233, 85, 123), "", "rosas"),
    (221, 239, 179): ColorInfo("0237", "Melocotón Cristal Forrado Brillante", "Lined Crystal Peach Luster", "DB0237", "Lined Crystal Peach Luster", (221, 239, 179), "", "verdes"),
    (69, 204, 188): ColorInfo("0238", "Verde Aguamarina Cristal Forrado Brillante", "Lined Crystal Green Aqua Luster", "DB0238", "Lined Crystal Green Aqua Luster", (69, 204, 188), "", "azules"),
    (223, 107, 190): ColorInfo("0239", "Verde Claro Aguamarina Ceilán", "Ceylon Light Aquamarine", "DB0239", "Ceylon Light Aqua", (223, 107, 190), "https://nguillers.com/miyuki-delica-10-0-ceylon-light-aqua-db0239-1-db0239.html", "rosas"),
    (100, 136, 213): ColorInfo("0240", "Azul Cielo Oscuro Ceilán", "Dark Sky Blue Ceylon", "DB0240", "Dark Sky Blue Ceylon", (100, 136, 213), "", "azules"),
    (159, 158, 172): ColorInfo("0242", "Gris Plateado Ceilán Brillante", "Ceylon Silver Gray Luster", "DB0242", "Ceylon Silver Gray Luster", (159, 158, 172), "", "grises"),
    (15, 18, 101): ColorInfo("0243", "Azul Cristal Medio Forrado y Teñido Ceilán", "Medium Crystal Blue Ceylon Lined-Dyed", "DB0243", "Medium Crystal Blue Ceylon Lined-Dyed", (15, 18, 101), "", "azules"),
    (254, 240, 245): ColorInfo("0244", "Rosa Ceilán", "Pink Ceylon", "DB0244", "Pink Ceylon", (254, 240, 245), "", "blancos"),
    (254, 209, 225): ColorInfo("0245", "Rosa Algodón de Azúcar Ceilán", "Cotton Candy Pink Ceylon", "DB0245", "Cotton Candy Pink Ceylon", (254, 209, 225), "", "rosas"),
    (255, 147, 208): ColorInfo("0246", "Rosa Algodón de Azúcar Oscuro Ceilán", "Dark Cotton Candy Pink Ceylon", "DB0246", "Dark Cotton Candy Pink Ceylon", (255, 147, 208), "", "rosas"),
    (207, 107, 190): ColorInfo("0247", "Fucsia Ceilán", "Ceylon Fuchsia", "DB0247", "Ceylon Fuchsia", (207, 107, 190), "https://nguillers.com/miyuki-delica-10-0-ceylon-fuchsia-db0247-1-db0247.html", "rosas"),
    (236, 190, 233): ColorInfo("0248", "Lila Pálido Cristal Forrado", "Lined Crystal Pale Lilac", "DB0248", "Lined Crystal Pale Lilac", (236, 190, 233), "", "morados"),
    (131, 96, 201): ColorInfo("0249", "Púrpura Ceilán", "Purple Ceylon", "DB0249", "Purple Ceylon", (131, 96, 201), "", "morados"),
    (104, 94, 138): ColorInfo("0250", "Amatista Ceilán", "Amethyst Ceylon", "DB0250", "Amethyst Ceylon", (104, 94, 138), "", "azules"),
    (164, 164, 163): ColorInfo("0251", "Gris Galvanizado Lustre", "Galvanized Gray Luster", "DB0251", "Galvanized Gray Luster", (164, 164, 163), "", "grises"),
    (187, 187, 187): ColorInfo("0252", "Gris Ceilán", "Ceylon Grey", "DB0252", "Ceylon Grey", (187, 187, 187), "", "grises"),
    (162, 114, 137): ColorInfo("0253", "Morado Malva Brillo Opaco Dorad", "Opaque Dark Orchid Luster", "DB0253", "Opaque Dark Orchid Luster", (162, 114, 137), "", "rosas"),
    (56, 61, 53): ColorInfo("0254", "Plata Deslustrada Galvanizada", "Galvanized Tarnished Silver", "DB0254", "Galvanized Tarnished Silver", (56, 61, 53), "", "grises"),
    (219, 204, 206): ColorInfo("0256", "Gris Rubor Forrado de Color Ceilán", "Ceylon Color Lined Blush", "DB0256", "Ceylon Color Lined Blush", (219, 204, 206), "", "blancos"),
    (199, 205, 229): ColorInfo("0257", "Azul Cielo Ceilán", "Sky Blue Ceylon", "DB0257", "Sky Blue Ceylon", (199, 205, 229), "", "azules"),
    (229, 221, 210): ColorInfo("0261", "Beige Lino Opaco Lustre", "Opaque Linen Luster", "DB0261", "Opaque Linen Luster", (229, 221, 210), "", "naranjas"),
    (179, 185, 102): ColorInfo("0262", "Verde Chartreuse Opaco Lustre", "Opaque Chartreuse Luster", "DB0262", "Opaque Chartreuse Luster", (179, 185, 102), "", "verdes"),
    (99, 102, 65): ColorInfo("0263", "Verde Militar Nacarado", "Opaque Cactus Luster", "DB0263", "Opaque Cactus Luster", (99, 102, 65), "", "verdes"),
    (67, 96, 100): ColorInfo("0264", "Azul Verdoso Opaco Lustre", "Opaque Mallard Luster", "DB0264", "Opaque Mallard Luster", (67, 96, 100), "", "azules"),
    (152, 125, 139): ColorInfo("0265", "Malva Opaco Lustre", "Opaque Mauve Luster", "DB0265", "Opaque Mauve Luster", (152, 125, 139), "", "rosas"),
    (129, 143, 179): ColorInfo("0266", "Azul Vaquero Opaco Lustre", "Opaque Denim Blue Luster", "DB0266", "Opaque Denim Blue Luster", (129, 143, 179), "", "azules"),
    (119, 127, 155): ColorInfo("0267", "Azul Opaco Brillo", "Opaque Blueberry Luster", "DB0267", "Opaque Blueberry Luster", (119, 127, 155), "", "azules"),
    (96, 98, 95): ColorInfo("0268", "Gris Oscuro Opaco Brillo", "Opaque Smoke Luster", "DB0268", "Opaque Smoke Luster", (96, 98, 95), "", "grises"),
    (213, 215, 213): ColorInfo("0271", "Gris Plata Brillante Cristal Forrado", "Sparkling Silver Gray Lined Crystal", "DB0271", "Sparkling Silver Gray Lined Crystal", (213, 215, 213), "", "grises"),
    (254, 194, 80): ColorInfo("0272", "Topacio Forrado Vara de Oro AB", "Goldenrod Lined Topaz AB", "DB0272", "Goldenrod Lined Topaz AB", (254, 194, 80), "", "naranjas"),
    (174, 178, 136): ColorInfo("0273", "Verde Oliva Transparente Línea Color", "Transparent Color Lined Olive Green", "DB0273", "Color Lined Olive", (174, 178, 136), "https://nguillers.com/miyuki-delica-10-0-color-lined-olive-db0273-1-db0273.html", "transparentes"),
    (52, 123, 55): ColorInfo("0274", "Verde Guisante Forrado Lustre", "Lined Pea Green Luster", "DB0274", "Lined Pea Green Luster", (52, 123, 55), "", "verdes"),
    (15, 49, 42): ColorInfo("0275", "Verde Azulado Forrado Teñido", "Green Teal Lined-Dyed", "DB0275", "Green Teal Lined-Dyed", (15, 49, 42), "", "verdes"),
    (43, 69, 84): ColorInfo("0276", "Verde Azulado Forrado AB", "Teal-Lined AB", "DB0276", "Teal-Lined AB", (43, 69, 84), "", "azules"),
    (45, 31, 83): ColorInfo("0277", "Azul Índigo Lustre", "Transparent Cobalt Luster", "DB0277", "Transparent Cobalt Luster", (45, 31, 83), "", "morados"),
    (45, 49, 112): ColorInfo("0278", "Azul Oscuro Forrado Teñido", "Lined Cobalt Luster", "DB0278", "Lined Cobalt Luster", (45, 49, 112), "", "azules"),
    (63, 25, 48): ColorInfo("0279", "Arándano Forrado Esmeralda Lustre", "Cranberry Lined Emerald Luster", "DB0279", "Cranberry Lined Emerald Luster", (63, 25, 48), "", "rosas"),
    (92, 47, 51): ColorInfo("0280", "Arándano Lustre de Cristal Forrado", "Cranberry Lined Crystal Luster", "DB0280", "Cranberry Lined Crystal Luster", (92, 47, 51), "", "rojos"),
    (118, 43, 118): ColorInfo("0281", "Fucsia Forrado Cristal Lustre", "Fuchsia Lined Crystal Luster", "DB0281", "Fuchsia Lined Crystal Luster", (118, 43, 118), "", "morados"),
    (148, 38, 57): ColorInfo("0282", "Topacio Claro Lustre Forrado de Arándano", "Cranberry Lined Light Topaz Luster", "DB0282", "Cranberry Lined Light Topaz Luster", (148, 38, 57), "", "rojos"),
    (188, 81, 97): ColorInfo("0283", "Rojo Ambar Oscuro Forrado de Color", "Color Lined Amber/Dark Red", "DB0283", "Color Lined Amber/Dark Red", (188, 81, 97), "", "rojos"),
    (67, 64, 121): ColorInfo("0284", "Púrpura Brillante Forrado en Aguamarina Lustre", "Sparkling Purple Lined Aqua Luster", "DB0284", "Sparkling Purple Lined Aqua Luster", (67, 64, 121), "", "azules"),
    (42, 106, 180): ColorInfo("0285", "Azul línea agua", "Blue Lined Aqua", "DB0285", "Blue Lined Aqua", (42, 106, 180), "", "azules"),
    (51, 68, 76): ColorInfo("0286", "Verde Esmeralda Brillante Forrado en Aqua Lustre", "Sparkling Emerald Lined Aqua Luster", "DB0286", "Sparkling Emerald Lined Aqua Luster", (51, 68, 76), "", "azules"),
    (127, 86, 66): ColorInfo("0287", "Marron Topacio lustre Forrado de Canela", "Cinnamon Lined Topaz Luster", "DB0287", "Cinnamon Lined Topaz Luster", (127, 86, 66), "", "marrones"),
    (255, 204, 141): ColorInfo("0288", "Ámbar Forrado de Plata Transparente AB", "Transparent Silver Lined Amber AB", "DB0288", "Transparent Silver Lined Amber AB", (255, 204, 141), "", "naranjas"),
    (218, 41, 59): ColorInfo("0295", "Rojo cereza Forrado AB", "Transparent Dark Cherry Color Lined Red AB", "DB0295", "Transparent Dark Cherry Color Lined Red AB", (218, 41, 59), "", "rojos"),
    (155, 45, 51): ColorInfo("0296", "Rojo Rubí Forrado AB", "Lined Ruby AB", "DB0296", "Lined Ruby AB", (155, 45, 51), "", "rojos"),
    (74, 32, 41): ColorInfo("0297", "Rojo Granate Forrado Rubí AB", "Garnet Lined Ruby AB", "DB0297", "Garnet Lined Ruby AB", (74, 32, 41), "", "rojos"),
    (91, 108, 144): ColorInfo("0301", "Gris Azul Metálico Mate Opaco Brillante", "Gray Blue Metallic Matte Opaque Luster", "DB0301", "Matte Metallic Gunmetal", (91, 108, 144), "https://nguillers.com/miyuki-delica-10-0-matte-metallic-gunmetal-db0301-1-db0301.html", "metalicos"),
    (83, 82, 88): ColorInfo("0306", "Gris Oscuro Mate", "Matte Metallic Slate", "DB0306", "Matte Metallic Slate", (83, 82, 88), "", "grises"),
    (89, 94, 95): ColorInfo("0307", "Gris Plata Metálico Mate", "Matte Metallic Silver Gray", "DB0307", "Matte Metallic Silver Gray", (89, 94, 95), "", "grises"),
    (19, 19, 19): ColorInfo("0310", "Negro Mate", "Matte Black", "DB0310", "Matte Black", (19, 19, 19), "https://nguillers.com/miyuki-delica-10-0-matte-black-db0310-1-db0310.html", "negros"),
    (78, 74, 68): ColorInfo("0311", "Verde Oliva Mate Metálico", "Matte Metallic Dark Olive", "DB0311", "Matte Metallic Dark Olive", (78, 74, 68), "", "verdes"),
    (91, 67, 67): ColorInfo("0312", "Rojo Frambuesa Oscuro Metálico Mate Iris", "Matte Metallic Dark Raspberry Iris", "DB0312", "Matte Metallic Dark Raspberry Iris", (91, 67, 67), "", "rojos"),
    (160, 153, 136): ColorInfo("0321", "Níquel Plateado Mate", "Matte Silver Nickel", "DB0321", "Matte Metallic Silver Nickel", (160, 153, 136), "https://nguillers.com/miyuki-delica-10-0-matte-metallic-silver-nickel-db0321-1-db0321.html", "naranjas"),
    (109, 90, 72): ColorInfo("0322", "Dorado DK Metálico Mate", "Metallic DK Gold Matte", "DB0322", "Matte Metallic Dark Gold", (109, 90, 72), "https://nguillers.com/miyuki-delica-10-0-matte-metallic-dark-gold-db0322-1-db0322.html", "metalicos"),
    (89, 72, 82): ColorInfo("0323", "Cobre Metálico Mate Arcoíris Iris", "Matte Metallic Copper Rainbow Iris", "DB0323", "Matte Metallic Copper Rainbow Iris", (89, 72, 82), "", "metalicos"),
    (117, 124, 102): ColorInfo("0324", "Verde Metálico Mate", "Matte Metallic Patina Iris", "DB0324", "Matte Metallic Patina Iris", (117, 124, 102), "", "verdes"),
    (44, 61, 79): ColorInfo("0325", "Azul Iris Metálico Mate", "Matte Metallic Blue Iris", "DB0325", "Matte Metallic Blue Iris", (44, 61, 79), "", "azules"),
    (44, 77, 46): ColorInfo("0327", "Verde Oscuro Metálico Mate Iris", "Matte Metallic Dark Green Iris", "DB0327", "Matte Metallic Dark Green Iris", (44, 77, 46), "", "verdes"),
    (255, 212, 117): ColorInfo("0331", "Oro Chapado en 24 Quilates Mate", "Matte 24kt Gold-Plated", "DB0331", "Matte 24kt Gold-Plated", (255, 212, 117), "", "amarillos"),
    (190, 157, 122): ColorInfo("0334", "Oro Amarillo Oscuro Metálico Mate", "Matte 24kt Gold Light Plated", "DB0334", "Matte 24kt Gold Light Plated", (190, 157, 122), "", "naranjas"),
    (249, 241, 222): ColorInfo("0335", "Plata Galvanizado Mate", "Matte Galvanized Silver", "DB0335", "Matte Galvanized Silver", (249, 241, 222), "", "blancos"),
    (165, 160, 163): ColorInfo("0338", "Plata Chapado en Paladio Mate", "Matte Palladium Plated", "DB0338", "Matte Palladium Plated", (165, 160, 163), "", "grises"),
    (255, 143, 127): ColorInfo("0340", "Cobre Metálico Mate", "Matte Copper Plated", "DB0340", "Matte Copper Plated", (255, 143, 127), "", "metalicos"),
    (255, 255, 255): ColorInfo("0351", "Blanco Mate", "Matte White", "DB0351", "Matte Chalk White AB", (255, 255, 255), "https://bisuteriabeads.com/producto/miyuki-delica-opaco-mate-blanco/", "blancos"),
    (250, 248, 243): ColorInfo("0352", "Cultura Marfil Opaco Mate", "Opaque Matte Cultured Ivory", "DB0352", "Opaque Matte Cultured Ivory", (250, 248, 243), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-cultured-ivory-db0352-1-db0352.html", "blancos"),
    (255, 240, 223): ColorInfo("0353", "Beige Opaco Mate", "Matte Opaque Beige", "DB0353", "Matte Opaque Beige", (255, 240, 223), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-light-brown-db0353-1-db0353.html", "naranjas"),
    (254, 233, 216): ColorInfo("0354", "Rosa Pálido Opaco Mate", "Matte Opaque Blush", "DB0354", "Matte Opaque Blush", (254, 233, 216), "", "rosas"),
    (192, 152, 174): ColorInfo("0355", "Rosa Mate", "Matte Opaque Dusty Orchid", "DB0355", "Matte Opaque Dusty Orchid", (192, 152, 174), "", "rosas"),
    (233, 220, 229): ColorInfo("0356", "Rosa Opaco Mate", "Matte Opaque Rose", "DB0356", "Matte Opaque Rose", (233, 220, 229), "", "rosas"),
    (130, 152, 228): ColorInfo("0361", "Azul Meridian  Opaco Mate AB", "Opaque Matte AB Meridian Blue", "DB0361", "Opaque Matte AB Meridian Blue", (130, 152, 228), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-ab-meridian-blue-db0361-1-db0361.html", "azules"),
    (227, 76, 121): ColorInfo("0362", "Rojo Opaco Mate Lustre", "Matte Opaque Red Luster", "DB0362", "Matte Opaque Red Luster", (227, 76, 121), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-ab-padparadscha-db0362-1-db0362.html", "rosas"),
    (153, 137, 93): ColorInfo("0371", "Verde Oliva Dorado Opaco Mate Lustre", "Matte Opaque Golden Olive Luster", "DB0371", "Matte Opaque Golden Olive Luster", (153, 137, 93), "", "verdes"),
    (159, 151, 90): ColorInfo("0372", "Verde Amarillo Claro Metálico Mate", "Matte Opaque Light Olive Luster", "DB0372", "Matte Opaque Light Olive Luster", (159, 151, 90), "", "verdes"),
    (78, 94, 90): ColorInfo("0373", "Verde Salvia Metálico Mate Lustre", "Matte Metallic Sage Green Luster", "DB0373", "Matte Metallic Sage Green Luster", (78, 94, 90), "", "verdes"),
    (161, 202, 189): ColorInfo("0374", "Azul Opaco Mate Lt", "Opaque Matte Lt Blue", "DB0374", "Opaque Matte Light Blue", (161, 202, 189), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-light-blue-db0374-1-db0374.html", "verdes"),
    (166, 227, 232): ColorInfo("0375", "Azul Turquesa Opaco Mate Lustre", "Matte Opaque Turquoise Blue Luster", "DB0375", "Matte Opaque Turquoise Blue Luster", (166, 227, 232), "", "azules"),
    (151, 181, 205): ColorInfo("0376", "Azul lustre Acero Metálico Mate", "Matte Metallic Steel Blue Luster", "DB0376", "Matte Metallic Steel Blue Luster", (151, 181, 205), "", "azules"),
    (123, 123, 180): ColorInfo("0377", "Azul Real Metálico Mate", "Matte Metallic Royal Blue", "DB0377", "Matte Metallic Royal Blue", (123, 123, 180), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-royal-blue-db0377-1-db0377.html", "metalicos"),
    (137, 59, 61): ColorInfo("0378", "Rojo Opaco Mate Brillante", "Matte Opaque Red Glazed Luster", "DB0378", "Matte Opaque Red Glazed Luster", (137, 59, 61), "https://magnoliabijou.com/es/biser-delica-db0378-matte-metalic-dark-maroon-5-gramm", "rojos"),
    (182, 154, 163): ColorInfo("0379", "Rosa Viejo Metálico Mate", "Matte Opaque Dusty Mauve Luster", "DB0379", "Matte Opaque Dusty Mauve Luster", (182, 154, 163), "", "rosas"),
    (153, 144, 116): ColorInfo("0380", "Verde Rosa Metálico Mate", "Matte Metallic Green Pink", "DB0380", "Matte Metallic Green Pink", (153, 144, 116), "", "verdes"),
    (136, 149, 169): ColorInfo("0381", "Gris Sombra Transparente Mate Lustre", "Matte Transparent Shadow Gray Luster", "DB0381", "Matte Transparent Shadow Gray Luster", (136, 149, 169), "", "azules"),
    (249, 242, 226): ColorInfo("0382", "Beige Topacio Pálido Mate Lustre", "Matte Transparent Pale Topaz Luster", "DB0382", "Matte Transparent Pale Topaz Luster", (249, 242, 226), "", "blancos"),
    (234, 231, 224): ColorInfo("0383", "Beige Lustre Transparente Mate Ostra", "Matte Transparent Oyster Luster", "DB0383", "Matte Transparent Oyster Luster", (234, 231, 224), "", "blancos"),
    (200, 190, 121): ColorInfo("0384-1", "Gris Marrón Ahumado Mate", "Matte Transparent Smoky Quartz Luster", "DB0384-1", "Matte Transparent Smoky Quartz Luster", (200, 190, 121), "", "naranjas"),
    (216, 240, 240): ColorInfo("0385", "Turquesa Ahumado Mate", "Matte Transparent Sea Glass Luster", "DB0385", "Matte Transparent Sea Glass Luster", (216, 240, 240), "", "azules"),
    (196, 195, 227): ColorInfo("0386", "Lila Seco Transparente Mate Lustre", "Matte Transparent Dried Lavender Luster", "DB0386", "Matte Transparent Dried Lavender Luster", (196, 195, 227), "", "morados"),
    (135, 169, 194): ColorInfo("0387", "Azul Zafiro Oscuro Satinado", "Matte Transparent Dark Cobalt Luster", "DB0387", "Matte Transparent Dark Cobalt Luster", (135, 169, 194), "", "azules"),
    (221, 209, 186): ColorInfo("0388", "Marfil Opaco Mate Lustre", "Matte Opaque Bone Luster", "DB0388", "Matte Opaque Bone Luster", (221, 209, 186), "", "naranjas"),
    (254, 212, 160): ColorInfo("0389", "Terracota Claro Opaco Mate", "Matte Opaque Light Terracotta", "DB0389", "Matte Opaque Light Terracotta", (254, 212, 160), "", "naranjas"),
    (204, 179, 124): ColorInfo("0390", "Verde Té Opaco Mate", "Matte Opaque Green Tea finish", "DB0390", "Matte Opaque Green Tea finish", (204, 179, 124), "", "naranjas"),
    (134, 148, 96): ColorInfo("0391", "Verde Opaco Mate", "Opaque Matte Green", "DB0391", "Opaque Matte Chartreuse", (134, 148, 96), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-chartreuse-db0391-1-db0391.html", "verdes"),
    (218, 166, 60): ColorInfo("0410", "Oro Amarillo Galvanizado", "Galvanized Yellow Gold", "DB0410", "Galvanized Yellow Gold", (218, 166, 60), "", "amarillos"),
    (232, 174, 112): ColorInfo("0411", "Oro Albaricoque Galvanizado", "Galvanized Apricot Gold", "DB0411", "Galvanized Apricot Gold", (232, 174, 112), "", "naranjas"),
    (240, 218, 129): ColorInfo("0412", "Amarillo Galvanizado", "Galvanized Yellow", "DB0412", "Galvanized Yellow", (240, 218, 129), "", "amarillos"),
    (194, 198, 145): ColorInfo("0413", "Verde Musgo Galvanizado", "Galvanized Moss Green", "DB0413", "Galvanized Moss Green", (194, 198, 145), "", "verdes"),
    (156, 189, 183): ColorInfo("0414", "Azul/Verde Teñido Galvanizado", "Galvanized Blue/Green Dyed", "DB0414", "Galvanized Blue/Green Dyed", (156, 189, 183), "", "azules"),
    (196, 211, 195): ColorInfo("0415", "Verde Turquesa Galvanizado", "Galvanized Turquoise Green", "DB0415", "Galvanized Turquoise Green", (196, 211, 195), "", "verdes"),
    (136, 165, 159): ColorInfo("0416", "Aguamarina Galvanizada", "Galvanized Aquamarine", "DB0416", "Galvanized Aquamarine", (136, 165, 159), "", "azules"),
    (228, 220, 214): ColorInfo("0417", "Malva Polvoriento Galvanizado", "Galvanized Dusty Mauve", "DB0417", "Galvanized Dusty Mauve", (228, 220, 214), "", "blancos"),
    (222, 179, 182): ColorInfo("0418", "Rosa Claro Galvanizado o Rosa Pálido Galvanizado", "Galvanized Light Rose", "DB0418", "Galvanized Light Rose", (222, 179, 182), "", "rosas"),
    (182, 96, 115): ColorInfo("0419", "Rosa Oscuro Galvanizado", "Galvanized Dusty Orchid", "DB0419", "Galvanized Dusty Orchid", (182, 96, 115), "", "rosas"),
    (216, 134, 167): ColorInfo("0420", "Rosa Galvanizado", "Galvanized Pink", "DB0420", "Galvanized Pink", (216, 134, 167), "", "rosas"),
    (200, 116, 35): ColorInfo("0421", "Naranja Mandarina Galvanizado", "Galvanized Tangerine", "DB0421", "Galvanized Tangerine", (200, 116, 35), "", "naranjas"),
    (204, 59, 159): ColorInfo("0422", "Fucsia Galvanizado", "Fuchsia Opaque Galvanized-Dyed", "DB0422", "Fuchsia Opaque Galvanized-Dyed", (204, 59, 159), "", "rosas"),
    (226, 132, 115): ColorInfo("0423", "Lila Galvanizado Teñido", "Galvanized Lilac Dyed", "DB0423", "Galvanized Lilac Dyed", (226, 132, 115), "", "rosas"),
    (248, 224, 104): ColorInfo("0424", "Amarillo Zest Opaco Galvanizado Teñido", "Purple Opaque Galvanized-Dyed", "DB0424", "Purple Opaque Galvanized-Dyed", (248, 224, 104), "", "amarillos"),
    (234, 122, 202): ColorInfo("0425", "Rosa Fuerte Galvanizado", "Galvanized Hot Pink", "DB0425", "Galvanized Hot Pink", (234, 122, 202), "", "rosas"),
    (143, 211, 178): ColorInfo("0426", "Verde Menta Oscuro Opaco Galvanizado", "Dark Mint Green Opaque Galvanized-Dyed", "DB0426", "Dark Mint Green Opaque Galvanized-Dyed", (143, 211, 178), "", "verdes"),
    (130, 196, 211): ColorInfo("0427", "Azul Lapis Opaco Galvanizado Teñido", "Lapis Opaque Galvanized-Dyed", "DB0427", "Lapis Opaque Galvanized-Dyed", (130, 196, 211), "", "azules"),
    (218, 108, 112): ColorInfo("0428", "Rojo Arándano Claro Opaco Galvanizado", "Light Cranberry Red Opaque Galvanized-Dyed", "DB0428", "Light Cranberry Red Opaque Galvanized-Dyed", (218, 108, 112), "", "rojos"),
    (229, 201, 194): ColorInfo("0429", "Rojo Arándano Opaco Galvanizado Teñido", "Cranberry Red Opaque Galvanized-Dyed", "DB0429", "Cranberry Red Opaque Galvanized-Dyed", (229, 201, 194), "", "rojos"),
    (200, 182, 224): ColorInfo("0430", "Púrpura Opaco Galvanizado Teñido", "Purple Opaque Galvanized-Dyed", "DB0430", "Purple Opaque Galvanized-Dyed", (200, 182, 224), "", "morados"),
    (196, 103, 197): ColorInfo("0431", "Fucsia Opaco Galvanizado Teñido", "Fuchsia Opaque Galvanized-Dyed", "DB0431", "Fuchsia Opaque Galvanized-Dyed", (196, 103, 197), "", "morados"),
    (124, 166, 172): ColorInfo("0432", "Azul Turquesa Metálico", "Turquoise Opaque Galvanized-Dyed", "DB0432", "Turquoise Opaque Galvanized-Dyed", (124, 166, 172), "", "azules"),
    (232, 212, 196): ColorInfo("0433", "Champaña Galvanizado", "Galvanized Champagne", "DB0433", "Galvanized Champagne", (232, 212, 196), "", "naranjas"),
    (237, 178, 137): ColorInfo("0434", "Naranja Damasco Galvanizado", "Apricot Opaque Galvanized-Dyed", "DB0434", "Apricot Opaque Galvanized-Dyed", (237, 178, 137), "", "naranjas"),
    (236, 202, 200): ColorInfo("0435", "Rosa Vibrante", "Rose Zest Opaque Galvanized-Dyed", "DB0435", "Rose Zest Opaque Galvanized-Dyed", (236, 202, 200), "", "rosas"),
    (202, 170, 129): ColorInfo("0436", "Oro Amarillo Opaco Galvanizado Teñido", "Yellow Gold Opaque Galvanized-Dyed", "DB0436", "Yellow Gold Opaque Galvanized-Dyed", (202, 170, 129), "", "naranjas"),
    (70, 87, 99): ColorInfo("0451", "Azul Petróleo Metálico", "Dark Steel Blue Opaque Galvanized-Dyed", "DB0451", "Dark Steel Blue Opaque Galvanized-Dyed", (70, 87, 99), "", "azules"),
    (61, 57, 51): ColorInfo("0452", "Café Caqui metalico", "Metallic Khaki", "DB0452", "Metallic Khaki", (61, 57, 51), "", "marrones"),
    (80, 80, 90): ColorInfo("0453", "Gris plomo", "Dark Gunmetal", "DB0453", "Dark Gunmetal", (80, 80, 90), "", "grises"),
    (132, 101, 108): ColorInfo("0454", "Purpura Amatista Ahumada Galvanizada", "Galvanized Smoky Amethyst", "DB0454", "Galvanized Smoky Amethyst", (132, 101, 108), "", "rosas"),
    (126, 103, 122): ColorInfo("0455", "Ciruela Oscura Galvanizada", "Galvanized Dark Plum", "DB0455", "Galvanized Olive", (126, 103, 122), "", "morados"),
    (223, 196, 128): ColorInfo("0456", "Oliva Galvanizado", "Galvanized Olive", "DB0456", "Galvanized Olive", (223, 196, 128), "", "amarillos"),
    (97, 101, 87): ColorInfo("0457", "Verde Acero Oscuro Galvanizado", "Galvanized Dark Steel Green", "DB0457", "Galvanized Dark Steel Green", (97, 101, 87), "", "verdes"),
    (62, 99, 96): ColorInfo("0458", "Verde Azulado Oscuro Galvanizado", "Galvanized Dark Teal Green", "DB0458", "Galvanized Dark Teal Green", (62, 99, 96), "", "verdes"),
    (36, 67, 88): ColorInfo("0459", "Azul Turquesa Oscuro Galvanizado", "Galvanized Dark Teal", "DB0459", "Galvanized Dark Teal", (36, 67, 88), "", "azules"),
    (125, 87, 90): ColorInfo("0460", "Oro Oscuro Galvanizado", "Galvanized Dark Gold", "DB0460", "Galvanized Dark Gold", (125, 87, 90), "", "rojos"),
    (162, 104, 68): ColorInfo("0461", "Oro Rosa Oscuro Galvanizado", "Galvanized Dark Rose Gold", "DB0461", "Galvanized Dark Rose Gold", (162, 104, 68), "", "naranjas"),
    (145, 122, 126): ColorInfo("0462", "Albaricoque Oscuro Galvanizado", "Galvanized Dark Apricot", "DB0462", "Galvanized Dark Apricot", (145, 122, 126), "", "rosas"),
    (112, 55, 104): ColorInfo("0463", "Rosa Oscuro Galvanizado", "Galvanized Dark Pink", "DB0463", "Galvanized Dark Pink", (112, 55, 104), "", "morados"),
    (92, 74, 94): ColorInfo("0464", "Rojo Oscuro Galvanizado", "Galvanized Dark Red", "DB0464", "Galvanized Dark Red", (92, 74, 94), "", "morados"),
    (34, 53, 63): ColorInfo("0465", "Azul media noche galvanizado", "Galvanized blue", "DB0465", "Galvanized blue", (34, 53, 63), "", "azules"),
    (45, 87, 90): ColorInfo("0607", "Teal Transparente Línea Plateada", "Transparent Teal Silver Line", "DB0607", "Silver Lined Teal", (45, 87, 90), "https://nguillers.com/miyuki-delica-10-0-silver-lined-teal-db0607-1-db0607.html", "transparentes"),
    (8, 190, 191): ColorInfo("0658", "Azul Turquesa Opaco", "Opaque Turquoise Blue", "DB0658", "Opaque Turquoise", (8, 190, 191), "https://nguillers.com/miyuki-delica-10-0-opaque-turquoise-db0658-1-db0658.html", "azules"),
    (105, 81, 102): ColorInfo("0662", "Morado Uva Opaco", "Opaque Grape Purple", "DB0662", "Opaque Grape", (105, 81, 102), "https://nguillers.com/miyuki-delica-10-0-opaque-grape-db0662-1-db0662.html", "morados"),
    (248, 221, 9): ColorInfo("0721", "Amarillo Opaco", "Opaque Yellow", "DB0721", "Opaque Yellow", (248, 221, 9), "https://nguillers.com/miyuki-delica-10-0-opaque-yellow-db0721-1-db0721.html", "amarillos"),
    (252, 109, 22): ColorInfo("0722", "Naranja Opaco", "Opaque Orange", "DB0722", "Opaque Orange", (252, 109, 22), "https://nguillers.com/miyuki-delica-10-0-opaque-orange-db0722-1-db0722.html", "naranjas"),
    (86, 160, 74): ColorInfo("0724", "Verde Opaco", "Opaque Green", "DB0724", "Opaque Green", (86, 160, 74), "https://nguillers.com/miyuki-delica-10-0-opaque-green-db0724-1-db0724.html", "verdes"),
    (97, 188, 233): ColorInfo("0725", "Azul Opaco Lt", "Opaque Lt Blue", "DB0725", "Opaque Lt Blue", (97, 188, 233), "https://nguillers.com/miyuki-delica-seed-bead-round-n-11-opaque-lt-blue-db0725-db0725.html", "azules"),
    (32, 37, 129): ColorInfo("0726", "Azul Royal Opaco", "Opaque Royal Blue", "DB0726", "Opaque Royal Blue", (32, 37, 129), "https://nguillers.com/miyuki-delica-10-0-opaque-royal-blue-db0726-1-db0726.html", "azules"),
    (217, 23, 22): ColorInfo("0727", "Coral Opaco", "Opaque Coral", "DB0727", "Opaque Coral", (217, 23, 22), "https://nguillers.com/miyuki-delica-10-0-opaque-coral-db0727-1-db0727.html", "rojos"),
    (203, 178, 204): ColorInfo("0728", "Lavanda Morado Opaco", "Opaque Purple Lavender", "DB0728", "Opaque Lavender", (203, 178, 204), "https://nguillers.com/miyuki-delica-10-0-opaque-lavender-db0728-1-db0728.html", "morados"),
    (122, 213, 211): ColorInfo("0729", "Verde Turquesa Opaco", "Opaque Turquoise Green", "DB0729", "Opaque Turquoise", (122, 213, 211), "https://nguillers.com/miyuki-delica-10-0-opaque-turquoise-db0729-1-db0729.html", "azules"),
    (144, 141, 217): ColorInfo("0730", "Azul Opaco", "Opaque Blue", "DB0730", "Opaque Azul", (144, 141, 217), "https://nguillers.com/miyuki-delica-seed-bead-round-n-11-opaque-blue-db0730-db0730.html", "azules"),
    (238, 215, 184): ColorInfo("0732", "Beige Marfil Opaco", "Opaque Ivory Beige", "DB0732", "Opaque Ivory", (238, 215, 184), "https://nguillers.com/miyuki-delica-10-0-opaque-ivory-db0732-1-db0732.html", "naranjas"),
    (88, 69, 72): ColorInfo("0734", "Café Oscuro Opaco", "Opaque Dark Brown", "DB0734", "Opaque Chocolate", (88, 69, 72), "https://nguillers.com/miyuki-delica-10-0-opaque-chocolate-db0734-1-db0734.html", "rojos"),
    (253, 253, 253): ColorInfo("0741", "Esmerilado Mate Cristal Transparente", "Crystal Transparent Frosted Matte", "DB0741", "Matte Crystal", (253, 253, 253), "https://nguillers.com/miyuki-delica-10-0-matte-crystal-db0741-1-db0741.html", "transparentes"),
    (252, 252, 252): ColorInfo("0750", "Blanco Mate Opaco", "Opaque Matte White", "DB0750", "Opaque Matte White", (252, 252, 252), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-white-db0750-1-db0750.html", "blancos"),
    (247, 85, 24): ColorInfo("0752", "Naranja Mate Opaco", "Opaque Matte Orange", "DB0752", "Opaque Matte Orange", (247, 85, 24), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-orange-db0752-1-db0752.html", "naranjas"),
    (214, 43, 41): ColorInfo("0753", "Rojo Opaco", "Opaque Red", "DB0753", "Opaque Red", (214, 43, 41), "https://nguillers.com/miyuki-delica-10-0-opaque-red-db0753-1-db0753.html", "rojos"),
    (65, 57, 134): ColorInfo("0756", "Azul Cobalto Mate Opaco", "Opaque Matte Cobalt Blue", "DB0756", "Opaque Matte Cobalt", (65, 57, 134), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-cobalt-db0756-1-db0756.html", "azules"),
    (19, 167, 91): ColorInfo("0767", "Verde Mate Transparente", "Matte Transparent Green", "DB0767", "Matte Transparent Green", (19, 167, 91), "https://nguillers.com/miyuki-delica-10-0-matte-transparent-green-db0767-1-db0767.html", "transparentes"),
    (96, 69, 58): ColorInfo("0769", "Café Mate Transparente", "Matte Transparent Brown", "DB0769", "Matte Transparent Brown", (96, 69, 58), "https://nguillers.com/miyuki-delica-10-0-matte-transparent-brown-db0769-1-db0769.html", "transparentes"),
    (226, 255, 154): ColorInfo("0775", "Scarlet Mate Transparente", "Matte Transparent Scarlet", "DB0775", "Matte Transparent Scarlet", (226, 255, 154), "https://nguillers.com/miyuki-delica-10-0-matte-transparent-scarlet-db0775-1-db0775.html", "transparentes"),
    (0, 239, 247): ColorInfo("0793", "Azul Turquesa Mate Opaco", "Opaque Matte Turquoise Blue", "DB0793", "Opaque Matte Turquoise", (0, 239, 247), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-turquoise-db0793-1-db0793.html", "azules"),
    (133, 76, 50): ColorInfo("0794", "Café Naranja Mate Opaco", "Opaque Matte Orange Brown", "DB0794", "Opaque Matte Rust", (133, 76, 50), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-rust-db0794-1-db0794.html", "naranjas"),
    (241, 118, 88): ColorInfo("0795", "Naranja Coral Mate Opaco", "Opaque Matte Orange Coral", "DB0795", "Opaque Matte Coral", (241, 118, 88), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-coral-db0795-1-db0795.html", "rojos"),
    (254, 226, 183): ColorInfo("0852", "Topacio Mate Transparent", "Transparent Matte Topaz", "DB0852", "Matte Transparent Topaz", (254, 226, 183), "https://nguillers.com/miyuki-delica-10-0-matte-transparent-topaz-db0852-1-db0852.html", "naranjas"),
    (153, 62, 6): ColorInfo("0853", "Topacio Oscuro Mate Transparente AB", "Transparent Matte AB Dark Topaz", "DB0853", "Matte Transparent AB Dark Topaz", (153, 62, 6), "https://nguillers.com/miyuki-delica-10-0-matte-transparent-ab-dark-topaz-db0853-1-db0853.html", "transparentes"),
    (244, 144, 91): ColorInfo("0855", "Naranja Hyacinth Mate Transparente AB", "Transparent Matte AB Orange Hyacinth", "DB0855", "Matte Transparent AB Hyacinth", (244, 144, 91), "https://nguillers.com/miyuki-delica-10-0-matte-transparent-ab-hyacinth-db0855-1-db0855.html", "transparentes"),
    (219, 86, 112): ColorInfo("0856", "Rojo Mate Transparente AB", "Transparent Matte Red AB", "DB0856", "Matte Transparent Red AB", (219, 86, 112), "https://nguillers.com/miyuki-delica-10-0-matte-transparent-red-ab-db0856-1-db0856.html", "transparentes"),
    (185, 167, 202): ColorInfo("0857", "Amatista Claro Mate Transparente AB", "Transparent Matte AB Light Amethyst", "DB0857", "Matte Transparent AB Light Amethyst", (185, 167, 202), "https://nguillers.com/miyuki-delica-10-0-matte-transparent-ab-light-amethyst-db0857-1-db0857.html", "transparentes"),
    (184, 219, 198): ColorInfo("0877", "Verde Lima Mate Opaco AB", "Opaque Matte AB Lime Green", "DB0877", "Opaque Matte AB Lime Green", (184, 219, 198), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-ab-lime-green-db0877-1-db0877.html", "verdes"),
    (195, 244, 241): ColorInfo("0878", "Verde Turquesa Mate Opaco AB", "Opaque Matte AB Turquoise Green", "DB0878", "Opaque Matte AB Turquoise", (195, 244, 241), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-ab-turquoise-db0878-1-db0878.html", "azules"),
    (169, 250, 253): ColorInfo("0879", "Azul Turquesa  Mate Opaco AB", "Opaque Matte Turquoise AB", "DB0879", "Opaque Matte AB Turquoise", (169, 250, 253), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-ab-turquoise-db0879-1-db0879.html", "azules"),
    (247, 241, 229): ColorInfo("0883", "Beige Marfil Mate Opaco", "Opaque Matte Beige Ivory", "DB0883", "Opaque Matte Ivory", (247, 241, 229), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-ivory-db0883-1-db0883.html", "blancos"),
    (252, 212, 0): ColorInfo("1132", "Amarillo Opaco", "Opaque Yellow", "DB1132", "Opaque Yellow", (252, 212, 0), "https://nguillers.com/miyuki-delica-10-0-opaque-yellow-db1132-1-db1132.html", "amarillos"),
    (120, 56, 59): ColorInfo("1134", "Café Rojizo Opaco", "Opaque Reddish Brown", "DB1134", "Opaque Brick Red", (120, 56, 59), "https://nguillers.com/miyuki-delica-10-0-opaque-brick-red-db1134-1-db1134.html", "rojos"),
    (178, 194, 245): ColorInfo("1137", "Azul Opaco", "Opaque Blue", "DB1137", "Opaque Blue", (178, 194, 245), "https://nguillers.com/miyuki-delica-seed-bead-round-n-11-opaque-blue-db1137-db1137.html", "azules"),
    (236, 69, 203): ColorInfo("1310", "Fucsia Transparente", "Transparent Fuchsia", "DB1310", "Transparent Dyed Fuchsia", (236, 69, 203), "https://nguillers.com/miyuki-delica-seed-bead-round-n-11-transparent-dyed-fuchsia-db1310-db1310.html", "transparentes"),
    (203, 87, 92): ColorInfo("1312", "Morado Transparente", "Transparent Purple", "DB1312", "Transparent Purple", (203, 87, 92), "https://nguillers.com/miyuki-delica-10-0-transparent-purple-db1312-1-db1312.html", "transparentes"),
    (158, 8, 118): ColorInfo("1340", "Fucsia Transparente Línea Plateada", "Transparent Fuchsia Silver Line", "DB1340", "Silver Lined Fuchsia", (158, 8, 118), "https://nguillers.com/miyuki-delica-10-0-silver-lined-fuchsia-db1340-1-db1340.html", "transparentes"),
    (145, 38, 145): ColorInfo("1345", "Morado Línea Plateada", "Purple Línea Plateada", "DB1345", "Purple Silver Line", (145, 38, 145), "https://nguillers.com/miyuki-delica-seed-bead-round-n-11-purple-silver-line-db1345-db1345.html", "morados"),
    (250, 192, 205): ColorInfo("1355", "Rosado Transparente Línea Plateada", "Transparent Pink Silver Line", "DB1355", "Silver Lined Pink", (250, 192, 205), "https://nguillers.com/miyuki-delica-10-0-silver-lined-pink-db1355-1-db1355.html", "transparentes"),
    (243, 200, 192): ColorInfo("1493", "Salmon Claro Glaseado Opaco", "Opaque Light Salmon Glazed", "DB1493", "Opaque Light Salmon Luster", (243, 200, 192), "https://nguillers.com/miyuki-delica-10-0-opaque-light-salmon-luster-db1493-1-db1493.html", "rojos"),
    (234, 215, 226): ColorInfo("1494", "Rosado Glaseado Opaco Lt", "Opaque Lt Pink Glazed", "DB1494", "Opaque Light Pink Luster", (234, 215, 226), "https://nguillers.com/miyuki-delica-10-0-opaque-light-pink-luster-db1494-1-db1494.html", "blancos"),
    (252, 246, 212): ColorInfo("1511", "Amarillo Pastel Mate Opaco", "Opaque Matte Pastel Yellow", "DB1511", "Opaque Matte Pastel Yellow", (252, 246, 212), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-pastel-yellow-db1511-1-db1511.html", "amarillos"),
    (227, 245, 226): ColorInfo("1516", "Verde Pastel Mate Opaco", "Opaque Matte Pastel Green", "DB1516", "Opaque Matte Pastel Green", (227, 245, 226), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-pastel-green-db1516-1-db1516.html", "blancos"),
    (239, 248, 255): ColorInfo("1517", "Azul Pastel Mate Opaco", "Opaque Matte Pastel Blue", "DB1517", "Opaque Matte Pastel Blue", (239, 248, 255), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-pastel-blue-db1517-1-db1517.html", "blancos"),
    (238, 241, 245): ColorInfo("1518", "Gris Pastel Mate Opaco", "Opaque Matte Pastel Gray", "DB1518", "Opaque Matte Pastel Gray", (238, 241, 245), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-pastel-gray-db1518-1-db1518.html", "blancos"),
    (255, 241, 187): ColorInfo("1531", "Amarillo Ceilán", "Ceylon Yellow", "DB1531", "Ceylon Yellow", (255, 241, 187), "https://nguillers.com/miyuki-delica-seed-bead-round-n-11-ceylon-yellow-db1531-1-db1531.html", "amarillos"),
    (236, 215, 217): ColorInfo("1534", "Palo De Rosa Ceilán", "Ceylon Palo De Rose", "DB1534", "Ceylon Pale Rose", (236, 215, 217), "https://nguillers.com/miyuki-delica-seed-bead-round-n-11-ceylon-pale-rose-db1534-1-db1534.html", "blancos"),
    (225, 241, 220): ColorInfo("1536", "Verde Menta Ceilán", "Ceylon Green Menta", "DB1536", "Ceylon Mint Green", (225, 241, 220), "https://nguillers.com/miyuki-delica-seed-bead-round-n-11-ceylon-mint-green-db1536-1-db1536.html", "blancos"),
    (228, 238, 250): ColorInfo("1537", "Azul Glaseado Ceilán", "Ceylon Blue Glazed", "DB1537", "Ceylon Blue", (228, 238, 250), "https://nguillers.com/miyuki-delica-seed-bead-round-n-11-ceylon-blue-db1537-1-db1537.html", "blancos"),
    (220, 219, 214): ColorInfo("1538", "Gris Glaseado Ceilán", "Ceylon Gray Glazed", "DB1538", "Ceylon Gray", (220, 219, 214), "https://nguillers.com/miyuki-delica-seed-bead-round-n-11-ceylon-gray-db1538-1-db1538.html", "blancos"),
    (254, 239, 204): ColorInfo("1560", "Beige Claro Perlado", "Beige Light Pearl", "DB1560", "Pearl Light Beige", (254, 239, 204), "https://nguillers.com/miyuki-delica-seed-bead-round-n-11-pearl-light-beige-db1560-db1560.html", "naranjas"),
    (94, 169, 172): ColorInfo("1576", "Verde Marino Opaco AB", "Seagreen Opaque AB", "DB1576", "Seagreen Opaque AB", (94, 169, 172), "", "azules"),
    (254, 229, 0): ColorInfo("1582", "Amarillo Canary Mate Opaco", "Opaque Matte Canary Yellow", "DB1582", "Opaque Matte Canary", (254, 229, 0), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-canary-db1582-1-db1582.html", "amarillos"),
    (252, 135, 20): ColorInfo("1583", "Naranja Mate Opaco", "Opaque Matte Orange", "DB1583", "Opaque Matte Orange", (252, 135, 20), "https://nguillers.com/miyuki-delica-10-0-opaque-matte-orange-db1583-1-db1583.html", "naranjas"),
    (19, 110, 228): ColorInfo("1764", "Verde esmeralda línea agua", "Emerald Line Acua", "BD1764", "Emerald Line Acua", (19, 110, 228), "", "azules"),
    (153, 236, 234): ColorInfo("1812", "Verde Agua Claro Satén de Seda Teñido", "Dyed Light Aqua Green Silk Satin", "BD1812", "Dyed Light Aqua Green Silk Satin", (153, 236, 234), "", "azules"),
    (201, 189, 139): ColorInfo("1831", "Plateado Mate Galvanizado Duracoat", "Galvanized Matte Silver Duracoat", "DB1831", "Duracoat Galvanized Matte Silver", (201, 189, 139), "https://nguillers.com/miyuki-delica-10-0-duracoat-galvanized-matte-silver-db1831-1-db1831.html", "amarillos"),
    (200, 160, 50): ColorInfo("1832", "Dorado Galvanizado Duracoat", "Duracoat Galvanized Gold", "DB1832", "Duracoat Galvanized Gold", (200, 160, 50), "", "naranjas"),
    (219, 191, 146): ColorInfo("1834", "Champagne Galvanizado Duracoat", "Galvanized Champagne Duracoat", "DB1834", "Duracoat Galvanized Champagne", (219, 191, 146), "https://nguillers.com/miyuki-delica-10-0-duracoat-galvanized-champagne-db1834-1-db1834.html", "naranjas"),
    (150, 86, 70): ColorInfo("1842", "Cobre Galvanizado Duracoat", "Galvanized Copper Duracoat", "DB1842", "Duracoat Galvanized Copper", (150, 86, 70), "https://nguillers.com/miyuki-delica-10-0-duracoat-galvanized-copper-db1842-1-db1842.html", "rojos"),
    (129, 98, 86): ColorInfo("1843", "Mauve Mate Galvanizado Duracoat", "Galvanized Matte Mauve Duracoat", "DB1843", "Duracoat Galvanized Matte Mauve", (129, 98, 86), "https://nguillers.com/miyuki-delica-10-0-duracoat-galvanized-matte-mauve-db1843-1-db1843.html", "naranjas"),
    (153, 61, 89): ColorInfo("1849", "Magenta Galvanizado Duracoat", "Magenta Galvanized Duracoat", "DB1849", "Magenta Galvanized Duracoat", (153, 61, 89), "https://nguillers.com/miyuki-delica-seed-bead-round-n-11-magenta-galvanizado-duracoat-db1849-db1849.html", "rosas"),
    (253, 252, 234): ColorInfo("1900", "Marfil Opaco Brillante", "Opaque Ivory Luster", "DB1900", "Opaque Ivory Luster", (253, 252, 234), "https://nguillers.com/miyuki-delica-10-0-opaque-ivory-luster-db1900-1-db1900.html", "blancos"),
    (254, 214, 242): ColorInfo("2036", "Fucsia Luminosa", "Luminous Fuchsia", "DB2036", "Luminous Fuchsia", (254, 214, 242), "https://nguillers.com/miyuki-delica-seed-bead-round-n-11-luminous-fuchsia-db2036-db2036.html", "rosas"),
    (173, 236, 196): ColorInfo("2040", "Verde Neón", "Neon Green", "DB2040", "Luminous Neon Green", (173, 236, 196), "https://nguillers.com/miyuki-delica-10-0-luminous-neon-green-db2040-1-db2040.html", "verdes"),
    (243, 171, 4): ColorInfo("2103", "Amarillo Ámbar Duracoat", "Yellow Amber Duracoat", "DB2103", "Duracoat Yellow Amber", (243, 171, 4), "https://nguillers.com/miyuki-delica-10-0-duracoat-yellow-amber-db2103-1-db2103.html", "naranjas"),
    (205, 174, 159): ColorInfo("2105", "Beige Duracoat Opaco", "Opaque Beige Duracoat", "DB2105", "Duracoat Opaque Beige", (205, 174, 159), "https://nguillers.com/miyuki-delica-10-0-duracoat-opaque-beige-db2105-1-db2105.html", "naranjas"),
    (216, 165, 75): ColorInfo("2106", "Hawthorne Opaco Duracoat", "Duracoat Opaque Hawthorne", "DB2106", "Duracoat Opaque Hawthorne", (216, 165, 75), "", "naranjas"),
    (215, 106, 95): ColorInfo("2114", "Rosado Duracoat Opaco", "Opaque Pink Duracoat", "DB2114", "Duracoat Opaque Pink", (215, 106, 95), "https://nguillers.com/miyuki-delica-10-0-duracoat-opaque-pink-db2114-1-db2114.html", "rojos"),
    (252, 166, 188): ColorInfo("2116", "Rosado Duracoat", "Pink Duracoat", "DB2116", "Duracoat Pink", (252, 166, 188), "https://nguillers.com/miyuki-delica-10-0-duracoat-pink-db2116-1-db2116.html", "rosas"),
    (116, 186, 10): ColorInfo("2121", "Verde Kiwi Duracoat Opaco", "Opaque Kiwi Green Duracoat", "DB2121", "Duracoat Opaque Kiwi", (116, 186, 10), "https://nguillers.com/miyuki-delica-10-0-duracoat-opaque-kiwi-db2121-1-db2121.html", "verdes"),
    (78, 196, 157): ColorInfo("2122", "Catalina Duracoat Opaco", "Duracoat Opaque Catalina", "DB2122", "Duracoat Opaque Catalina", (78, 196, 157), "https://nguillers.com/miyuki-delica-10-0-duracoat-opaque-catalina-db2122-1-db2122.html", "verdes"),
    (70, 150, 132): ColorInfo("2125", "Verde Opal Duracoat Opaco", "Opaque Opal Green Duracoat", "DB2125", "Duracoat Opaque Opal Green", (70, 150, 132), "https://nguillers.com/miyuki-delica-10-0-duracoat-opaque-opal-green-db2125-1-db2125.html", "azules"),
    (89, 165, 137): ColorInfo("2127", "Verde Duracoat Opaco", "Opaque Green Duracoat", "DB2127", "Duracoat Opaque Green", (89, 165, 137), "https://nguillers.com/miyuki-delica-10-0-duracoat-opaque-green-db2127-1-db2127.html", "verdes"),
    (171, 225, 235): ColorInfo("2128", "Turquesa Duracoat Lt", "Light Turquoise Duracoat", "DB2128", "Duracoat Light Turquoise", (171, 225, 235), "https://nguillers.com/miyuki-delica-10-0-duracoat-light-turquoise-db2128-1-db2128.html", "azules"),
    (12, 140, 212): ColorInfo("2134", "Azul Duracoat Opaco", "Opaque Blue Duracoat", "DB2134", "Duracoat Opaque Blue", (12, 140, 212), "https://nguillers.com/miyuki-delica-10-0-duracoat-opaque-blue-db2134-1-db2134.html", "azules"),
    (68, 128, 170): ColorInfo("2135", "Azul Oscuro Opaco", "Duracoat Opaque Dark Imperial Blue", "DB2135", "Duracoat Opaque Dark Imperial Blue", (68, 128, 170), "https://nguillers.com/miyuki-delica-10-0-duracoat-opaque-blue-db2135-1-db2135.html", "azules"),
    (152, 100, 180): ColorInfo("2140", "Morado Duracoat Opaco", "Opaque Purple Duracoat", "DB2140", "Duracoat Opaque Purple", (152, 100, 180), "https://nguillers.com/miyuki-delica-10-0-duracoat-opaque-purple-db2140-1-db2140.html", "morados"),
    (170, 105, 47): ColorInfo("2142", "Marrón Duracoat Opaco", "Opaque Brown Duracoat", "DB2142", "Opaque Brown Duracoat", (170, 105, 47), "https://nguillers.com/miyuki-delica-seed-bead-round-n11-opaque-brown-duracoat-db2142-db2142.html", "naranjas"),
    (40, 44, 78): ColorInfo("2143", "Azul Marino Duracoat Opaco", "Opaque Blue Marino Duracoat", "DB2143", "Opaque Navy Blue Duracoat", (40, 44, 78), "https://nguillers.com/miyuki-delica-seed-bead-round-n11-opaque-navy-blue-duracoat-db2143-db2143.html", "azules"),
    (186, 4, 53): ColorInfo("2154", "Rosado Transparente Línea Plateada Duracoat", "Transparent Pink Línea Plateada Duracoat", "DB2154", "Pink Silver Line Duracoat", (186, 4, 53), "https://nguillers.com/miyuki-delica-seed-bead-round-n-11-pink-silver-line-duracoat-db2154-db2154.html", "transparentes"),
    (236, 66, 151): ColorInfo("2174", "Rosado Transparente Línea Plateada Duracoat", "Transparent Pink Línea Plateada Duracoat", "DB2174", "Pink Silver Line Duracoat", (236, 66, 151), "https://nguillers.com/miyuki-delica-seed-bead-round-n-11-pink-silver-line-duracoat-db2174-db2174.html", "transparentes"),
    (25, 58, 90): ColorInfo("2192", "Montana Transparente SL", "Transparent Montana Silver Line", "DB2192", "Silver Lined Montana", (25, 58, 90), "https://nguillers.com/miyuki-delica-10-0-silver-lined-montana-db2192-1-db2192.html", "transparentes"),
    (10, 14, 16): ColorInfo("2261", "Negro Picasso Opaco", "Opaque Black Picasso", "DB2261", "Opaque Black Picasso", (10, 14, 16), "https://nguillers.com/miyuki-delica-seed-bead-round-n-11-opaque-black-picasso-db2261-db2261.html", "azules"),
    (206, 205, 158): ColorInfo("2262", "Amarillo Picasso Opaco", "Opaque Yellow Picasso", "DB2262", "Opaque Yellow Picasso", (206, 205, 158), "https://nguillers.com/miyuki-delica-10-0-opaque-yellow-picasso-db2262-1-db2262.html", "amarillos"),
    (121, 185, 183): ColorInfo("2264", "Azul Turquesa Picasso Opaco", "Opaque Turquoise Blue Picasso", "DB2264", "Opaque Turquoise Picasso", (121, 185, 183), "https://nguillers.com/miyuki-delica-10-0-opaque-turquoise-picasso-db2264-1-db2264.html", "azules"),
    (157, 131, 90): ColorInfo("2267", "Marrón Picasso Opaco", "Opaque Brown Picasso", "DB2267", "Opaque Brown Picasso", (157, 131, 90), "https://nguillers.com/miyuki-delica-10-0-opaque-brown-picasso-db2267-1-db2267.html", "naranjas"),
    (217, 120, 146): ColorInfo("2353", "Morado Duracoat Opaco", "Opaque Purple Duracoat", "DB2353", "Duracoat Opaque Purple", (217, 120, 146), "https://nguillers.com/miyuki-delica-10-0-duracoat-opaque-purple-db2353-1-db2353.html", "rosas"),
    (109, 105, 106): ColorInfo("2368", "Gris Charcoal Duracoat", "Charcoal Gray Duracoat", "DB2368", "Duracoat Charcoal Gray", (109, 105, 106), "https://nguillers.com/miyuki-delica-10-0-duracoat-charcoal-gray-db2368-1-db2368.html", "grises"),
    (218, 200, 118): ColorInfo("2502", "Dorado Brillante Galvanizado Duracoat", "Bright Gold Galvanized Duracoat", "DB2502", "Duracoat Galvanized Gold", (218, 200, 118), "https://nguillers.com/miyuki-delica-10-0-duracoat-galvanized-gold-db2502-1-db2502.html", "amarillos"),
    (222, 165, 155): ColorInfo("2503", "Oro Rosa Galvanizado Duracoat", "Oro Rose Galvanized Duracoat", "DB2503", "Galvanized Duracoat Shiny Copper", (222, 165, 155), "https://nguillers.com/miyuki-delica-seed-bead-round-n11-galvanized-duracoat-shiny-copper-db2503-db2503.html", "rojos"),
    (184, 156, 128): ColorInfo("2504", "Champagne Brillante Galvanizado Duracoat", "Bright Champagne Galvanized Duracoat", "DB2504", "Duracoat Galvanized Champagne", (184, 156, 128), "https://nguillers.com/miyuki-delica-10-0-duracoat-galvanized-champagne-db2504-1-db2504.html", "naranjas"),
    (52, 128, 102): ColorInfo("2506", "Verde Brillante Galvanizado Duracoat", "Bright Green Galvanized Duracoat", "DB2506", "Duracoat Galvanized Bright Green", (52, 128, 102), "https://nguillers.com/miyuki-delica-10-0-duracoat-galvanized-bright-green-db2506-1-db2506.html", "verdes"),
    (31, 31, 28): ColorInfo("2507", "Negro Brillante Galvanizado Duracoat", "Black Shiny Galvanized Duracoat", "DB2507", "Galvanized Duracoat Shiny Black", (31, 31, 28), "https://nguillers.com/miyuki-delica-seed-bead-round-n11-galvanized-duracoat-shiny-black-db2507-db2507.html", "negros"),
    (126, 99, 146): ColorInfo("2509", "Morado Brillante Galvanizado Duracoat", "Bright Purple Galvanized Duracoat", "DB2509", "Duracoat Galvanized Bright Purple", (126, 99, 146), "https://nguillers.com/miyuki-delica-10-0-duracoat-galvanized-bright-purple-db2509-1-db2509.html", "morados"),
    (99, 65, 132): ColorInfo("2510", "Morado Brillante Galvanizado Duracoat", "Purple Shiny Galvanized Duracoat", "DB2510", "Galvanized Duracoat Shiny Purple", (99, 65, 132), "https://nguillers.com/miyuki-delica-seed-bead-round-n11-galvanized-duracoat-shiny-purple-db2510-db2510.html", "morados"),
}

# Convertir a wrappers para agregar propiedades calculadas
MIYUKI_COLORS = {rgb: ColorInfoWrapper(info) for rgb, info in MIYUKI_COLORS_RAW.items()}

print(f"✅ Loaded {len(MIYUKI_COLORS)} Miyuki Delica colors from Nguillers Colombia")
print(f"   📸 100% RGB extraídos de fotografías reales de productos")

# ============================================================================
# COLOR MATCHING FUNCTIONS
# ============================================================================

def color_distance(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
    """Calculate Euclidean distance between two RGB colors"""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

def find_closest_color(target_color: Tuple[int, int, int], color_mode: str = 'miyuki'):
    """Find closest color in the selected palette"""
    # print(f"🎨 find_closest_color llamado con mode: '{color_mode}'")
    palette = MIYUKI_COLORS if color_mode == 'miyuki' else RGB_UNIVERSAL_COLORS
    # print(f"📦 Usando paleta: {'MIYUKI' if color_mode == 'miyuki' else 'RGB'} con {len(palette)} colores")
    
    if target_color in palette:
        return palette[target_color]
    
    min_distance = float('inf')
    closest_color = None
    
    for color_rgb, color_info in palette.items():
        distance = color_distance(target_color, color_rgb)
        if distance < min_distance:
            min_distance = distance
            closest_color = color_info
    
    # Return default based on mode
    if closest_color:
        return closest_color
    elif color_mode == 'miyuki':
        return ColorInfo("???", "Color desconocido", "???", target_color)
    else:
        hex_code = '#{:02x}{:02x}{:02x}'.format(*target_color)
        return ColorInfoRGB("???", "Unknown", hex_code, target_color)

# ============================================================================
# IMAGE PROCESSING FUNCTIONS
# ============================================================================

BEAD_TYPES = {
    'delica': {'bead_width_mm': 1.3, 'bead_height_mm': 1.6},
}

def get_bead_dimensions_mm(bead_type: str):
    """Return (bead_width_mm, bead_height_mm) for a given bead type."""
    bead = BEAD_TYPES.get(bead_type, BEAD_TYPES['delica'])
    return bead['bead_width_mm'], bead['bead_height_mm']

def calculate_bead_dimensions(width_cm: float, height_cm: float, bead_width_mm: float, bead_height_mm: float) -> Tuple[int, int]:
    """Calculate pattern dimensions in beads"""
    width_beads = round((width_cm * 10) / bead_width_mm)
    height_beads = round((height_cm * 10) / bead_height_mm)
    return width_beads, height_beads

def pixelate_image(image: Image.Image, target_width: int, target_height: int, num_colors: int = 10, 
                   saturation: float = 1.0, brightness: float = 1.0, contrast: float = 1.0, 
                   sharpness: float = 1.0, color_mode: str = 'miyuki') -> Image.Image:
                   
    """
    Convert image to pixelated pattern using selected color palette.
    This ensures visual pattern matches exactly with color guide.

    Args:
        saturation: 0.0 (grayscale) to 2.0 (very saturated), default 1.0
        brightness: 0.0 (black) to 2.0 (very bright), default 1.0
        contrast: 0.0 (gray) to 2.0 (high contrast), default 1.0
        sharpness: 0.0 (blurred) to 2.0 (sharp), default 1.0
        color_mode: 'miyuki' or 'rgb', default 'miyuki'
    """

    print(f"🖼️ pixelate_image - color_mode recibido: '{color_mode}'") 

    # Convert to RGB
    image = image.convert('RGB')
    
    # Apply color adjustments BEFORE resizing
    if saturation != 1.0:
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(saturation)
    
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(brightness)
    
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(contrast)
    
    if sharpness != 1.0:
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(sharpness)
    
    # Resize to target dimensions
    img_small = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    print(f"🔍 pixelate_image resize: {image.size} -> {img_small.size}")
    
    # Get palette based on mode
    palette = MIYUKI_COLORS if color_mode == 'miyuki' else RGB_UNIVERSAL_COLORS
    miyuki_palette = np.array(list(palette.keys()))  # ← REEMPLAZA la línea de MIYUKI_COLORS
    
    # Use k-means to find N dominant colors in the image
    kmeans = KMeans(n_clusters=min(num_colors, len(miyuki_palette)), random_state=42, n_init=10)
    
    # Get image pixels
    pixels = np.array(img_small)
    original_shape = pixels.shape
    pixels_flat = pixels.reshape(-1, 3)
    
    # Step 1: Find dominant colors in the image
    kmeans.fit(pixels_flat)
    dominant_colors = kmeans.cluster_centers_
    
    # Step 2: Map each dominant color to closest color in selected palette
    selected_colors = []  # ← Cambiar nombre (ya no solo Miyuki)
    for dominant_color in dominant_colors:
        closest_color = find_closest_color(tuple(dominant_color.astype(int)), color_mode)  # ← Usar nueva función
        if closest_color.rgb not in [tuple(c) for c in selected_colors]:  # ← Cambiar nombre variable
            selected_colors.append(list(closest_color.rgb))

    selected_colors = np.array(selected_colors)  # ← Cambiar nombre

    # Step 3: Map each pixel to closest selected color
    result_pixels = np.zeros_like(pixels_flat)
    for i, pixel in enumerate(pixels_flat):
        distances = np.sqrt(np.sum((selected_colors - pixel) ** 2, axis=1))  # ← Cambiar nombre
        closest_idx = np.argmin(distances)
        result_pixels[i] = selected_colors[closest_idx]  # ← Cambiar nombre

    # Reshape back to image
    result_pixels = result_pixels.reshape(original_shape).astype(np.uint8)
    result_image = Image.fromarray(result_pixels, 'RGB')
    
    return result_image

def create_grid_pattern(pattern: Image.Image, cell_width: int = 20, cell_height: int = 25, show_grid: bool = True) -> Image.Image:
    """Create pattern with optional grid overlay"""
    pixel_width, pixel_height = pattern.size
    
    canvas_width = pixel_width * cell_width
    canvas_height = pixel_height * cell_height
    grid_img = Image.new('RGB', (canvas_width, canvas_height), 'white')
    draw = ImageDraw.Draw(grid_img)
    
    pixels = pattern.load()
    for y in range(pixel_height):
        for x in range(pixel_width):
            color = pixels[x, y]
            x1 = x * cell_width
            y1 = y * cell_height
            x2 = x1 + cell_width
            y2 = y1 + cell_height
            
            if show_grid:
                if x == 0 and y == 0:  # Solo log del primer pixel
                    print(f"🎨 Dibujando grid - outline=(220, 220, 220)")
                # Draw with grid lines
                draw.rectangle([x1, y1, x2, y2], fill=color, outline=(220, 220, 220), width=1)
            else:
                # Draw without grid lines
                draw.rectangle([x1, y1, x2, y2], fill=color, outline=None)
    
    return grid_img

def create_peyote_pattern(pattern: Image.Image, cell_width: int = 20, cell_height: int = 25, show_grid: bool = True) -> Image.Image:
    """Create pattern in peyote stitch format (staggered columns - vertical offset)"""
    pixel_width, pixel_height = pattern.size
    
    # En peyote, las columnas pares están desplazadas 0.5 celdas HACIA ABAJO
    canvas_width = pixel_width * cell_width
    canvas_height = int((pixel_height + 0.5) * cell_height)
    peyote_img = Image.new('RGB', (canvas_width, canvas_height), 'white')
    draw = ImageDraw.Draw(peyote_img, mode='RGB')
    
    pixels = pattern.load()
    for y in range(pixel_height):
        for x in range(pixel_width):
            color = pixels[x, y]
            
            # Calcular desplazamiento VERTICAL: columnas pares (0, 2, 4...) no se desplazan
            # columnas impares (1, 3, 5...) se desplazan 0.5 celdas HACIA ABAJO
            offset_y = (cell_height // 2) if (x % 2 == 1) else 0
            
            x1 = x * cell_width
            y1 = y * cell_height + offset_y
            x2 = x1 + cell_width
            y2 = y1 + cell_height
            
            if show_grid:
                if x == 0 and y == 0:
                    print(f"🎨 Dibujando peyote VERTICAL - outline=(220, 220, 220)")
                draw.rectangle([x1, y1, x2, y2], fill=color, outline=(220, 220, 220), width=1)
            else:
                draw.rectangle([x1, y1, x2, y2], fill=color, outline=None)  
                
    return peyote_img

def get_contrast_color(rgb_color: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """
    Retorna blanco o negro según la luminosidad del color de fondo
    Para máximo contraste
    """
    r, g, b = rgb_color
    # Calcular luminosidad percibida (fórmula estándar)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    
    # Si es oscuro, usar blanco; si es claro, usar negro
    return (255, 255, 255) if luminance < 0.5 else (0, 0, 0)

def analyze_pattern_colors(pattern: Image.Image, color_mode: str = 'miyuki') -> dict:
    pixels = list(pattern.getdata())
    color_counts = {}
    
    for pixel in pixels:
        if pixel in color_counts:
            color_counts[pixel] += 1
        else:
            color_counts[pixel] = 1
    
    total_beads = sum(color_counts.values())
    
    color_analysis = []
    for color_rgb, count in sorted(color_counts.items(), key=lambda x: x[1], reverse=True):
        color_info = find_closest_color(color_rgb, color_mode)
        percentage = (count / total_beads) * 100
        
        if color_mode == 'miyuki':
            color_analysis.append({
                "code": color_info.code,
                "name": color_info.name,
                "miyuki": color_info.miyuki,
                "rgb": list(color_info.rgb),
                "count": int(count),
                "percentage": round(percentage, 1)
            })
        else:  # RGB mode
            color_analysis.append({
                "code": color_info.code,
                "name": color_info.name,
                "hex": color_info.hex,
                "rgb": list(color_info.rgb),
                "count": int(count),
                "percentage": round(percentage, 1)
            })
    
    return {
        "colors": color_analysis,
        "unique_colors": len(color_analysis),
        "total_beads": total_beads,
        "color_mode": color_mode
    }

def generate_row_guide(pattern: Image.Image, color_mode: str = 'miyuki') -> dict:
    """Generate row-by-row assembly guide with exact bead sequence"""
    width, height = pattern.size
    rows = []
    
    for y in range(height):
        row_pixels = [pattern.getpixel((x, y)) for x in range(width)]
        
        # Build exact sequence (left to right)
        sequence = []
        current_code = None
        current_count = 0
        
        for pixel in row_pixels:
            color_tuple = tuple(int(c) for c in pixel)
            color_info = find_closest_color(color_tuple, color_mode)
            code = color_info.code
            
            if code == current_code:
                current_count += 1
            else:
                if current_code is not None:
                    sequence.append({"code": current_code, "count": current_count})
                current_code = code
                current_count = 1
        
        if current_code is not None:
            sequence.append({"code": current_code, "count": current_count})
        
        # Calculate totals per color
        row_colors = [tuple(int(c) for c in pixel) for pixel in row_pixels]
        color_counts = {}
        for color in row_colors:
            color_info = find_closest_color(color, color_mode)
            code = color_info.code
            color_counts[code] = color_counts.get(code, 0) + 1
        
        totals = [{"code": code, "count": count} for code, count in color_counts.items()]
        
        rows.append({
            "row": y + 1,
            "sequence": sequence,
            "totals": totals
        })
    
    return {"rows": rows}

# ============================================================================
# PDF GENERATION FUNCTIONS
# ============================================================================

def generate_color_guide_pdf(colors: list, pattern_info: dict, color_mode: str = 'miyuki', lang: str = 'es') -> bytes:
    """Generate PDF color guide"""
    # Translations
    tr = {
        'es': {
            'domain':       'easycuentas.com',
            'brand':        'Easy Cuentas',
            'title_miyuki': 'GUÍA DE COLORES - CUENTAS MIYUKI',
            'title_rgb':    'GUÍA DE COLORES - RGB UNIVERSAL',
            'pattern':      'Patrón',
            'total':        'Total',
            'colors':       'colores',
            'unit_miyuki':  'cuentas',
            'unit_rgb':     'píxeles',
            'col_code':     'Código',
            'col_name':     'Nombre',
            'col_qty':      'Cantidad',
            'footer_miyuki':'IMPORTANTE: Códigos Miyuki son aproximados - verifica colores antes de comprar',
            'footer_rgb':   'Códigos Hex para referencia - Compatible con cualquier marca de cuentas',
        },
        'en': {
            'domain':       'myeasybeads.com',
            'brand':        'My Easy Beads',
            'title_miyuki': 'COLOR GUIDE - MIYUKI BEADS',
            'title_rgb':    'COLOR GUIDE - UNIVERSAL RGB',
            'pattern':      'Pattern',
            'total':        'Total',
            'colors':       'colors',
            'unit_miyuki':  'beads',
            'unit_rgb':     'pixels',
            'col_code':     'Code',
            'col_name':     'Name',
            'col_qty':      'Qty',
            'footer_miyuki':'IMPORTANT: Miyuki codes are approximate - verify colors before purchasing',
            'footer_rgb':   'Hex codes for reference - Compatible with any bead brand',
        }
    }
    t = tr.get(lang, tr['es'])
    buffer = io.BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # AGREGAR LOGO Y HEADER
    try:
        logo_path = 'easy-cuentas-logo.png'
        c.drawImage(logo_path, 30*mm, height - 28*mm, width=12*mm, height=12*mm, preserveAspectRatio=True, mask='auto')
    except:
        pass

    # Easy Cuentas al lado del logo
    c.setFont("Helvetica-Bold", 20)
    c.setFillColorRGB(0, 0.808, 0.82)  # Color turquesa como en la web
    c.drawString(45*mm, height - 23*mm, t['brand'])

    # easycuentas.com debajo
    c.setFillColorRGB(0, 0, 0)  # Negro
    c.setFont("Helvetica", 9)
    c.drawString(45*mm, height - 28*mm, t['domain'])

    # Título del documento
    c.setFont("Helvetica-Bold", 14)
    title = t['title_miyuki'] if color_mode == 'miyuki' else t['title_rgb']
    c.drawString(30*mm, height - 38*mm, title)
    
    unit = t['unit_miyuki'] if color_mode == 'miyuki' else t['unit_rgb']
    c.drawString(30*mm, height - 47*mm,
                 f"{t['pattern']}: {pattern_info['width']}x{pattern_info['height']} {unit} | "
                 f"{t['total']}: {pattern_info['total_beads']} {unit} | {len(colors)} {t['colors']}")
    
    # Table
    y = height - 65*mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(30*mm, y, 'Color')
    c.drawString(50*mm, y, t['col_code'])
    c.drawString(80*mm, y, t['col_name'])
    
    # CAMBIAR header según modo:
    if color_mode == 'miyuki':
        c.drawString(130*mm, y, "Miyuki")
    else:
        c.drawString(130*mm, y, "Hex")  # ← CAMBIAR para RGB

    c.drawString(165*mm, y, t['col_qty'])
    c.drawString(185*mm, y, "%")
    
    y -= 5*mm
    c.setFont("Helvetica", 8)
    
    for color in colors:
        if y < 30*mm:
            c.showPage()
            y = height - 30*mm
            c.setFont("Helvetica", 8)
        
        # Color swatch
        c.setFillColorRGB(color['rgb'][0]/255, color['rgb'][1]/255, color['rgb'][2]/255)
        c.rect(30*mm, y-3*mm, 15*mm, 4*mm, fill=1, stroke=1)

        # Text - alineado verticalmente con la caja
        text_y = y - 1.9*mm  # Centrar texto con la caja
        c.setFillColorRGB(0, 0, 0)
        c.drawString(50*mm, text_y, color['code'])
        c.drawString(80*mm, text_y, color['name'][:25])

        if color_mode == 'miyuki':
            c.drawString(130*mm, text_y, color['miyuki'])
        else:
            c.drawString(130*mm, text_y, color.get('hex', ''))

        c.drawString(165*mm, text_y, str(color['count']))
        c.drawString(185*mm, text_y, f"{color['percentage']}%")

        # AGREGAR: Línea separadora
        c.setStrokeColorRGB(0.85, 0.85, 0.85)  # Gris claro
        c.setLineWidth(0.5)
        c.line(30*mm, y-4*mm, 195*mm, y-4*mm)  # Línea horizontal
        
        y -= 6*mm
    
    # Footer
    c.setFont("Helvetica-Oblique", 7)
    c.drawString(30*mm, 15*mm, t['brand'] + " - " + t['domain'])
    
    # CAMBIAR footer según modo:
    if color_mode == 'miyuki':
        c.drawString(30*mm, 10*mm, t['footer_miyuki'])
    else:
        c.drawString(30*mm, 10*mm, t['footer_rgb'])
    
    c.save()
    return buffer.getvalue()

def generate_assembly_guide_pdf(rows: list, pattern_info: dict, color_mode: str = 'miyuki', lang: str = 'es') -> bytes:
    """Generate PDF assembly guide"""
    # Translations
    tr = {
        'es': {
            'domain':   'easycuentas.com',
            'brand':    'Easy Cuentas',
            'title':    'GUÍA DE MONTAJE POR FILA',
            'pattern':  'Patrón',
            'codes':    'Códigos',
            'qty':      'x cantidad',
            'unit':     'cuentas',
            'row':      'Fila',
            'footer':   'Secuencia: izquierda \u2192 derecha | Easy Cuentas - easycuentas.com',
        },
        'en': {
            'domain':   'myeasybeads.com',
            'brand':    'My Easy Beads',
            'title':    'ROW-BY-ROW ASSEMBLY GUIDE',
            'pattern':  'Pattern',
            'codes':    'Codes',
            'qty':      'x quantity',
            'unit':     'beads',
            'row':      'Row',
            'footer':   'Sequence: left → right | My Easy Beads - myeasybeads.com',
        }
    }
    t = tr.get(lang, tr['es'])
    buffer = io.BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # AGREGAR LOGO Y HEADER
    try:
        logo_path = 'easy-cuentas-logo.png'
        c.drawImage(logo_path, 30*mm, height - 28*mm, width=12*mm, height=12*mm, preserveAspectRatio=True, mask='auto')
    except:
        pass

    # Easy Cuentas al lado del logo
    c.setFont("Helvetica-Bold", 20)
    c.setFillColorRGB(0, 0.808, 0.82)  # Color turquesa
    c.drawString(45*mm, height - 23*mm, t['brand'])

    # easycuentas.com debajo
    c.setFillColorRGB(0, 0, 0)  # Negro
    c.setFont("Helvetica", 9)
    c.drawString(45*mm, height - 28*mm, t['domain'])

    # Título del documento
    c.setFont("Helvetica-Bold", 14)
    c.drawString(30*mm, height - 38*mm, t['title'])

    # Info del patrón
    c.setFont("Helvetica", 10)

    unit_label = 'Miyuki' if color_mode == 'miyuki' else 'RGB'
    c.drawString(30*mm, height - 47*mm, f"{t['pattern']}: {pattern_info['width']}x{pattern_info['height']} {t['unit']} | {t['codes']}: {unit_label} {t['qty']}")
    
    y = height - 55*mm
    c.setFont("Helvetica", 8)
    
    for row in rows:
        if y < 40*mm:
            c.showPage()
            y = height - 30*mm
            c.setFont("Helvetica", 8)
        
        # Row header
        c.setFont("Helvetica-Bold", 9)
        c.drawString(30*mm, y, f"{t['row']} {row['row']}:")
        
        # Totals
        totals_text = ", ".join([f"{t['code']}:{t['count']}" for t in row['totals']])
        c.setFont("Helvetica", 7)
        c.drawString(50*mm, y, totals_text)
        
        y -= 5*mm
        
        # Sequence
        c.setFont("Helvetica", 7)
        sequence_text = " → ".join([f"[{s['code']} × {s['count']}]" for s in row['sequence']])
        c.drawString(35*mm, y, sequence_text[:100])
        
        y -= 8*mm
    
    # Footer
    c.setFont("Helvetica-Oblique", 7)
    c.drawString(30*mm, 15*mm, t['footer'])
    
    c.save()
    return buffer.getvalue()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/generate', methods=['POST'])
def generate_pattern():
    """Generate pattern from uploaded image"""
    try:
        data = request.get_json()
        
        # Get parameters
        image_data = data.get('image')
        width_cm = float(data.get('width', 5.0))
        height_cm = float(data.get('height', 5.0))
        bead_type = data.get('beadType', 'delica')
        bead_width_mm, bead_height_mm = get_bead_dimensions_mm(bead_type)
        show_grid = data.get('showGrid', True)  # ← DEBE ESTAR ESTO
        num_colors = int(data.get('numColors', 10))
        print(f"🔍 Backend recibió showGrid: {show_grid}")
        show_numbers = data.get('showNumbers', False)  # ← AGREGAR AQUÍ
        print(f"🔍 Backend recibió showNumbers: {show_numbers}")
        color_mode = data.get('colorMode', 'miyuki')
        skip_quantization = data.get('skipQuantization', False)
        print(f"🔍 Backend recibió skipQuantization: {data.get('skipQuantization')} -> {skip_quantization}")  # NUEVA LÍNEA
        pattern_type = data.get('pattern_type', 'grid')  # default 'grid'
        
        # Color adjustment parameters
        saturation = float(data.get('saturation', 1.2))
        brightness = float(data.get('brightness', 1.0))
        contrast = float(data.get('contrast', 1.1))
        sharpness = float(data.get('sharpness', 1.0))
        
        # Decode image
        image_bytes = base64.b64decode(image_data.split(',')[1])
        image = Image.open(io.BytesIO(image_bytes))

        # Calculate dimensions
        width_beads, height_beads = calculate_bead_dimensions(width_cm, height_cm, bead_width_mm, bead_height_mm)
        
        # AGREGAR ESTE PRINT TEMPORAL
        print(f"🔍 DIAGNÓSTICO:")
        print(f"  - skip_quantization: {skip_quantization}")
        print(f"  - pattern_type: {pattern_type}")
        print(f"  - Imagen recibida: {image.size}")
        print(f"  - width_beads calculado: {width_beads}")
        print(f"  - height_beads calculado: {height_beads}")

        # Generate pixelated pattern
        if skip_quantization:
            # Imagen viene del editor - hacer downsample a dimensiones en beads
            print(f"🎨 Skip quantization - downsampling de {image.size} a ({width_beads}, {height_beads})")
            pattern = image.resize((width_beads, height_beads), Image.NEAREST)
        else:
            pattern = pixelate_image(image, width_beads, height_beads, num_colors, 
                                    saturation, brightness, contrast, sharpness, color_mode)

        # Create pattern images (sin coordenadas - frontend las dibujará)
        if skip_quantization:
            print(f"🎨 Modo EDICIÓN - regenerando con pattern_type={pattern_type}")
            if pattern_type == 'peyote':
                grid_pattern = create_peyote_pattern(pattern, cell_width=20, cell_height=25, show_grid=False)
            else:
                grid_pattern = create_grid_pattern(pattern, cell_width=20, cell_height=25, show_grid=False)
        elif pattern_type == 'peyote':
            print(f"🎨 Generando patrón PEYOTE")
            grid_pattern = create_peyote_pattern(pattern, cell_width=20, cell_height=25, show_grid=False)
        else:
            print(f"🎨 Generando patrón CUADRÍCULA")
            grid_pattern = create_grid_pattern(pattern, cell_width=20, cell_height=25, show_grid=False)

        # Analyze colors
        color_analysis = analyze_pattern_colors(pattern, color_mode)
        
        # Generate row guide
        row_guide = generate_row_guide(pattern, color_mode)
        
        # Convert images to base64
        def image_to_base64(img):
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode()
        
        # Construir respuesta
        response = {
            "success": True,
            "pattern": {
                "width": int(width_beads),
                "height": int(height_beads),
                "total_beads": int(width_beads * height_beads)
            },
            "images": {
                "grid": f"data:image/png;base64,{image_to_base64(grid_pattern)}",
                "basic": f"data:image/png;base64,{image_to_base64(grid_pattern)}"  # Usar grid_pattern directamente
            },
            "colors": color_analysis,
            "rowGuide": row_guide,
            "pattern_type": pattern_type
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/generate-color-guide-pdf', methods=['POST'])
def generate_color_guide_pdf_endpoint():
    """Generate color guide as PDF"""
    try:
        data = request.get_json()
        colors = data.get('colors', [])
        pattern_info = data.get('patternInfo', {})
        color_mode = data.get('colorMode', 'miyuki')
        lang = data.get('lang', 'es')
        
        pdf_bytes = generate_color_guide_pdf(colors, pattern_info, color_mode, lang)
        pdf_base64 = base64.b64encode(pdf_bytes).decode()
        
        return jsonify({
            "success": True,
            "pdf": f"data:application/pdf;base64,{pdf_base64}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/generate-assembly-guide', methods=['POST'])
def generate_assembly_guide_endpoint():
    """Generate assembly guide as PDF"""
    try:
        data = request.get_json()
        rows = data.get('rows', [])
        pattern_info = data.get('patternInfo', {})
        color_mode = data.get('colorMode', 'miyuki')
        lang = data.get('lang', 'es')
        
        pdf_bytes = generate_assembly_guide_pdf(rows, pattern_info, color_mode, lang)
        pdf_base64 = base64.b64encode(pdf_bytes).decode()
        
        return jsonify({
            "success": True,
            "pdf": f"data:application/pdf;base64,{pdf_base64}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "message": "Miyuki Pattern Generator API",
        "colors_loaded": len(MIYUKI_COLORS)
    })

@app.route('/api/get-palette', methods=['POST'])
def get_palette_endpoint():
    """Get complete color palette based on mode"""
    try:
        data = request.get_json()
        color_mode = data.get('colorMode', 'miyuki')
        
        palette = MIYUKI_COLORS if color_mode == 'miyuki' else RGB_UNIVERSAL_COLORS
        
        # Convert palette to list format
        palette_list = []
        for color_rgb, color_info in palette.items():
            if color_mode == 'miyuki':
                palette_list.append({
                    "code": color_info.code,
                    "name": color_info.name,
                    "miyuki": color_info.miyuki,
                    "rgb": list(color_info.rgb),
                    "category": color_info.category  # ← AGREGAR ESTA LÍNEA
                })
            else:
                palette_list.append({
                    "code": color_info.code,
                    "name": color_info.name,
                    "hex": color_info.hex,
                    "rgb": list(color_info.rgb),
                    "category": color_info.category  # ← AGREGAR ESTA LÍNEA
                })
        
        return jsonify({
            "success": True,
            "palette": palette_list,
            "color_mode": color_mode,
            "total_colors": len(palette_list)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        data = request.get_json()
        price_id = data.get('priceId')  # monthly o yearly
        user_email = data.get('email')
        
        # Determinar dominio según origen del request
        origin = request.headers.get('Origin', 'https://easycuentas.com')
        if 'myeasybeads' in origin:
            base_url = 'https://myeasybeads.com'
        else:
            base_url = 'https://easycuentas.com'

        # Crear sesión de Stripe Checkout
        checkout_session = stripe.checkout.Session.create(
            customer_email=user_email,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f'{base_url}/?payment=success',
            cancel_url=f'{base_url}/?payment=cancel',
        )
        
        return jsonify({'sessionId': checkout_session.id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        # Verificar firma del webhook
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Manejar eventos de suscripción
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session['customer_email']
        subscription_id = session['subscription']
        
        print(f"✅ Pago exitoso para: {customer_email}")
        print(f"   Subscription ID: {subscription_id}")
        
        try:
            # Buscar usuario por email en Firestore
            users_ref = db.collection('users')
            query = users_ref.where('email', '==', customer_email).limit(1)
            docs = query.stream()
            
            user_doc = None
            for doc in docs:
                user_doc = doc
                break
            
            if user_doc:
                # Actualizar plan a premium
                users_ref.document(user_doc.id).update({
                    'plan': 'premium',
                    'subscriptionId': subscription_id,
                    'subscriptionStatus': 'active'
                })
                print(f"✅ Usuario actualizado a Premium: {user_doc.id}")
            else:
                print(f"⚠️ Usuario no encontrado: {customer_email}")
                
        except Exception as e:
            print(f"❌ Error actualizando Firestore: {e}")

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        subscription_id = subscription['id']
        
        print(f"⚠️ Suscripción cancelada: {subscription_id}")
        
        try:
            # Buscar usuario por subscriptionId en Firestore
            users_ref = db.collection('users')
            query = users_ref.where('subscriptionId', '==', subscription_id).limit(1)
            docs = query.stream()
            
            user_doc = None
            for doc in docs:
                user_doc = doc
                break
            
            if user_doc:
                # Downgrade a Free
                users_ref.document(user_doc.id).update({
                    'plan': 'free',
                    'subscriptionStatus': 'canceled'
                })
                print(f"✅ Usuario downgradeado a Free: {user_doc.id}")
            else:
                print(f"⚠️ Usuario no encontrado con subscriptionId: {subscription_id}")
                
        except Exception as e:
            print(f"❌ Error downgrading usuario: {e}")
               
    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    print("=" * 60)
    print("🎨 MIYUKI PATTERN GENERATOR - STARTED")
    print("=" * 60)
    print(f"✅ Loaded {len(MIYUKI_COLORS)} Miyuki colors")
    print(f"   - Real colors from photos: {len(MIYUKI_REAL_COLORS)}")
    print(f"   - Manual essential colors: {len(MIYUKI_MANUAL_COLORS)}")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
