"""
RGB UNIVERSAL COLOR PALETTE
200 colors: 140 CSS standard + 60 essential extras (skin tones, grays, etc.)
"""

from collections import namedtuple

ColorInfo = namedtuple('ColorInfo', ['code', 'name', 'hex', 'rgb'])

# CSS Standard Colors (140 colors with names)
RGB_CSS_COLORS = {
    # Reds
    (255, 0, 0): ColorInfo("RED", "Red", "#FF0000", (255, 0, 0)),
    (139, 0, 0): ColorInfo("DRED", "DarkRed", "#8B0000", (139, 0, 0)),
    (220, 20, 60): ColorInfo("CRIM", "Crimson", "#DC143C", (220, 20, 60)),
    (255, 99, 71): ColorInfo("TOMA", "Tomato", "#FF6347", (255, 99, 71)),
    (255, 69, 0): ColorInfo("ORNG", "OrangeRed", "#FF4500", (255, 69, 0)),
    (255, 160, 122): ColorInfo("LSAL", "LightSalmon", "#FFA07A", (255, 160, 122)),
    (250, 128, 114): ColorInfo("SALM", "Salmon", "#FA8072", (250, 128, 114)),
    (233, 150, 122): ColorInfo("DSAL", "DarkSalmon", "#E9967A", (233, 150, 122)),
    (178, 34, 34): ColorInfo("FRED", "FireBrick", "#B22222", (178, 34, 34)),
    (165, 42, 42): ColorInfo("BROW", "Brown", "#A52A2A", (165, 42, 42)),
    (128, 0, 0): ColorInfo("MARO", "Maroon", "#800000", (128, 0, 0)),
    
    # Pinks
    (255, 192, 203): ColorInfo("PINK", "Pink", "#FFC0CB", (255, 192, 203)),
    (255, 182, 193): ColorInfo("LPNK", "LightPink", "#FFB6C1", (255, 182, 193)),
    (255, 105, 180): ColorInfo("HPNK", "HotPink", "#FF69B4", (255, 105, 180)),
    (255, 20, 147): ColorInfo("DPNK", "DeepPink", "#FF1493", (255, 20, 147)),
    (219, 112, 147): ColorInfo("PPNK", "PaleVioletRed", "#DB7093", (219, 112, 147)),
    (199, 21, 133): ColorInfo("MPNK", "MediumVioletRed", "#C71585", (199, 21, 133)),
    
    # Oranges
    (255, 165, 0): ColorInfo("ORNG", "Orange", "#FFA500", (255, 165, 0)),
    (255, 140, 0): ColorInfo("DORG", "DarkOrange", "#FF8C00", (255, 140, 0)),
    (255, 127, 80): ColorInfo("CORL", "Coral", "#FF7F50", (255, 127, 80)),
    
    # Yellows
    (255, 255, 0): ColorInfo("YELW", "Yellow", "#FFFF00", (255, 255, 0)),
    (255, 255, 224): ColorInfo("LYEL", "LightYellow", "#FFFFE0", (255, 255, 224)),
    (255, 250, 205): ColorInfo("LMON", "LemonChiffon", "#FFFACD", (255, 250, 205)),
    (250, 250, 210): ColorInfo("LGLW", "LightGoldenrodYellow", "#FAFAD2", (250, 250, 210)),
    (255, 239, 213): ColorInfo("PPWH", "PapayaWhip", "#FFEFD5", (255, 239, 213)),
    (255, 228, 181): ColorInfo("MOCA", "Moccasin", "#FFE4B5", (255, 228, 181)),
    (255, 218, 185): ColorInfo("PCHP", "PeachPuff", "#FFDAB9", (255, 218, 185)),
    (238, 232, 170): ColorInfo("PGLW", "PaleGoldenrod", "#EEE8AA", (238, 232, 170)),
    (240, 230, 140): ColorInfo("KHAK", "Khaki", "#F0E68C", (240, 230, 140)),
    (189, 183, 107): ColorInfo("DKHA", "DarkKhaki", "#BDB76B", (189, 183, 107)),
    (255, 215, 0): ColorInfo("GOLD", "Gold", "#FFD700", (255, 215, 0)),
    
    # Greens
    (0, 255, 0): ColorInfo("LIME", "Lime", "#00FF00", (0, 255, 0)),
    (0, 128, 0): ColorInfo("GREN", "Green", "#008000", (0, 128, 0)),
    (0, 100, 0): ColorInfo("DGRN", "DarkGreen", "#006400", (0, 100, 0)),
    (34, 139, 34): ColorInfo("FGRN", "ForestGreen", "#228B22", (34, 139, 34)),
    (144, 238, 144): ColorInfo("LGRN", "LightGreen", "#90EE90", (144, 238, 144)),
    (152, 251, 152): ColorInfo("PGRN", "PaleGreen", "#98FB98", (152, 251, 152)),
    (143, 188, 143): ColorInfo("DSGN", "DarkSeaGreen", "#8FBC8F", (143, 188, 143)),
    (60, 179, 113): ColorInfo("MSGN", "MediumSeaGreen", "#3CB371", (60, 179, 113)),
    (46, 139, 87): ColorInfo("SGRN", "SeaGreen", "#2E8B57", (46, 139, 87)),
    (0, 255, 127): ColorInfo("SPRG", "SpringGreen", "#00FF7F", (0, 255, 127)),
    (0, 250, 154): ColorInfo("MSPG", "MediumSpringGreen", "#00FA9A", (0, 250, 154)),
    (124, 252, 0): ColorInfo("LGRN", "LawnGreen", "#7CFC00", (124, 252, 0)),
    (127, 255, 0): ColorInfo("CHRT", "Chartreuse", "#7FFF00", (127, 255, 0)),
    (173, 255, 47): ColorInfo("GYLW", "GreenYellow", "#ADFF2F", (173, 255, 47)),
    (154, 205, 50): ColorInfo("YGRN", "YellowGreen", "#9ACD32", (154, 205, 50)),
    (107, 142, 35): ColorInfo("OLGR", "OliveGreen", "#6B8E23", (107, 142, 35)),
    (128, 128, 0): ColorInfo("OLIV", "Olive", "#808000", (128, 128, 0)),
    (85, 107, 47): ColorInfo("DOLV", "DarkOliveGreen", "#556B2F", (85, 107, 47)),
    
    # Cyans/Aquas
    (0, 255, 255): ColorInfo("CYAN", "Cyan", "#00FFFF", (0, 255, 255)),
    (0, 255, 255): ColorInfo("AQUA", "Aqua", "#00FFFF", (0, 255, 255)),
    (224, 255, 255): ColorInfo("LCYN", "LightCyan", "#E0FFFF", (224, 255, 255)),
    (175, 238, 238): ColorInfo("PTRQ", "PaleTurquoise", "#AFEEEE", (175, 238, 238)),
    (127, 255, 212): ColorInfo("AQUM", "Aquamarine", "#7FFFD4", (127, 255, 212)),
    (64, 224, 208): ColorInfo("TURQ", "Turquoise", "#40E0D0", (64, 224, 208)),
    (72, 209, 204): ColorInfo("MTRQ", "MediumTurquoise", "#48D1CC", (72, 209, 204)),
    (0, 206, 209): ColorInfo("DTRQ", "DarkTurquoise", "#00CED1", (0, 206, 209)),
    (32, 178, 170): ColorInfo("LSGR", "LightSeaGreen", "#20B2AA", (32, 178, 170)),
    (0, 139, 139): ColorInfo("DCYN", "DarkCyan", "#008B8B", (0, 139, 139)),
    (0, 128, 128): ColorInfo("TEAL", "Teal", "#008080", (0, 128, 128)),
    
    # Blues
    (0, 0, 255): ColorInfo("BLUE", "Blue", "#0000FF", (0, 0, 255)),
    (0, 0, 139): ColorInfo("DBLU", "DarkBlue", "#00008B", (0, 0, 139)),
    (0, 0, 128): ColorInfo("NAVY", "Navy", "#000080", (0, 0, 128)),
    (25, 25, 112): ColorInfo("MNBL", "MidnightBlue", "#191970", (25, 25, 112)),
    (173, 216, 230): ColorInfo("LBLU", "LightBlue", "#ADD8E6", (173, 216, 230)),
    (176, 224, 230): ColorInfo("PWBL", "PowderBlue", "#B0E0E6", (176, 224, 230)),
    (135, 206, 250): ColorInfo("LSKY", "LightSkyBlue", "#87CEFA", (135, 206, 250)),
    (135, 206, 235): ColorInfo("SKYB", "SkyBlue", "#87CEEB", (135, 206, 235)),
    (0, 191, 255): ColorInfo("DSKY", "DeepSkyBlue", "#00BFFF", (0, 191, 255)),
    (30, 144, 255): ColorInfo("DODG", "DodgerBlue", "#1E90FF", (30, 144, 255)),
    (100, 149, 237): ColorInfo("CORN", "CornflowerBlue", "#6495ED", (100, 149, 237)),
    (70, 130, 180): ColorInfo("STBL", "SteelBlue", "#4682B4", (70, 130, 180)),
    (176, 196, 222): ColorInfo("LSTL", "LightSteelBlue", "#B0C4DE", (176, 196, 222)),
    (65, 105, 225): ColorInfo("ROYL", "RoyalBlue", "#4169E1", (65, 105, 225)),
    (0, 0, 205): ColorInfo("MBLU", "MediumBlue", "#0000CD", (0, 0, 205)),
    
    # Purples
    (128, 0, 128): ColorInfo("PURP", "Purple", "#800080", (128, 0, 128)),
    (75, 0, 130): ColorInfo("INDI", "Indigo", "#4B0082", (75, 0, 130)),
    (138, 43, 226): ColorInfo("BVIO", "BlueViolet", "#8A2BE2", (138, 43, 226)),
    (148, 0, 211): ColorInfo("DVIO", "DarkViolet", "#9400D3", (148, 0, 211)),
    (153, 50, 204): ColorInfo("DORC", "DarkOrchid", "#9932CC", (153, 50, 204)),
    (186, 85, 211): ColorInfo("MVIO", "MediumViolet", "#BA55D3", (186, 85, 211)),
    (147, 112, 219): ColorInfo("MPUR", "MediumPurple", "#9370DB", (147, 112, 219)),
    (216, 191, 216): ColorInfo("THST", "Thistle", "#D8BFD8", (216, 191, 216)),
    (221, 160, 221): ColorInfo("PLUM", "Plum", "#DDA0DD", (221, 160, 221)),
    (238, 130, 238): ColorInfo("VIOL", "Violet", "#EE82EE", (238, 130, 238)),
    (255, 0, 255): ColorInfo("MGNT", "Magenta", "#FF00FF", (255, 0, 255)),
    (218, 112, 214): ColorInfo("ORCH", "Orchid", "#DA70D6", (218, 112, 214)),
    (199, 21, 133): ColorInfo("MVOR", "MediumOrchid", "#C71585", (199, 21, 133)),
    (230, 230, 250): ColorInfo("LAVD", "Lavender", "#E6E6FA", (230, 230, 250)),
    (255, 240, 245): ColorInfo("LBLS", "LavenderBlush", "#FFF0F5", (255, 240, 245)),
    
    # Whites
    (255, 255, 255): ColorInfo("WHTE", "White", "#FFFFFF", (255, 255, 255)),
    (255, 250, 250): ColorInfo("SNOW", "Snow", "#FFFAFA", (255, 250, 250)),
    (240, 255, 240): ColorInfo("HNYD", "Honeydew", "#F0FFF0", (240, 255, 240)),
    (245, 255, 250): ColorInfo("MINT", "MintCream", "#F5FFFA", (245, 255, 250)),
    (240, 255, 255): ColorInfo("AZUR", "Azure", "#F0FFFF", (240, 255, 255)),
    (240, 248, 255): ColorInfo("ALBL", "AliceBlue", "#F0F8FF", (240, 248, 255)),
    (248, 248, 255): ColorInfo("GHWH", "GhostWhite", "#F8F8FF", (248, 248, 255)),
    (245, 245, 245): ColorInfo("WSMK", "WhiteSmoke", "#F5F5F5", (245, 245, 245)),
    (255, 245, 238): ColorInfo("SSHL", "Seashell", "#FFF5EE", (255, 245, 238)),
    (245, 245, 220): ColorInfo("BEIG", "Beige", "#F5F5DC", (245, 245, 220)),
    (253, 245, 230): ColorInfo("OWHD", "OldLace", "#FDF5E6", (253, 245, 230)),
    (255, 250, 240): ColorInfo("FLWH", "FloralWhite", "#FFFAF0", (255, 250, 240)),
    (250, 235, 215): ColorInfo("AWHD", "AntiqueWhite", "#FAEBD7", (250, 235, 215)),
    (250, 240, 230): ColorInfo("LINN", "Linen", "#FAF0E6", (250, 240, 230)),
    (255, 228, 225): ColorInfo("MROS", "MistyRose", "#FFE4E1", (255, 228, 225)),
    
    # Grays
    (220, 220, 220): ColorInfo("GYTL", "Gainsboro", "#DCDCDC", (220, 220, 220)),
    (211, 211, 211): ColorInfo("LGRY", "LightGray", "#D3D3D3", (211, 211, 211)),
    (192, 192, 192): ColorInfo("SLVR", "Silver", "#C0C0C0", (192, 192, 192)),
    (169, 169, 169): ColorInfo("DGRY", "DarkGray", "#A9A9A9", (169, 169, 169)),
    (128, 128, 128): ColorInfo("GRAY", "Gray", "#808080", (128, 128, 128)),
    (105, 105, 105): ColorInfo("DMGY", "DimGray", "#696969", (105, 105, 105)),
    (119, 136, 153): ColorInfo("LSGY", "LightSlateGray", "#778899", (119, 136, 153)),
    (112, 128, 144): ColorInfo("SLGY", "SlateGray", "#708090", (112, 128, 144)),
    (47, 79, 79): ColorInfo("DSGY", "DarkSlateGray", "#2F4F4F", (47, 79, 79)),
    (0, 0, 0): ColorInfo("BLCK", "Black", "#000000", (0, 0, 0)),
    
    # Browns
    (210, 180, 140): ColorInfo("TAN", "Tan", "#D2B48C", (210, 180, 140)),
    (188, 143, 143): ColorInfo("ROSY", "RosyBrown", "#BC8F8F", (188, 143, 143)),
    (244, 164, 96): ColorInfo("SBRN", "SandyBrown", "#F4A460", (244, 164, 96)),
    (222, 184, 135): ColorInfo("BURL", "Burlywood", "#DEB887", (222, 184, 135)),
    (210, 105, 30): ColorInfo("CHOC", "Chocolate", "#D2691E", (210, 105, 30)),
    (139, 69, 19): ColorInfo("SDBR", "SaddleBrown", "#8B4513", (139, 69, 19)),
    (160, 82, 45): ColorInfo("SIENA", "Sienna", "#A0522D", (160, 82, 45)),
    (205, 133, 63): ColorInfo("PERU", "Peru", "#CD853F", (205, 133, 63)),
    (245, 222, 179): ColorInfo("WHEA", "Wheat", "#F5DEB3", (245, 222, 179)),
    (255, 228, 196): ColorInfo("BSQU", "Bisque", "#FFE4C4", (255, 228, 196)),
    (255, 235, 205): ColorInfo("BLNC", "BlanchedAlmond", "#FFEBCD", (255, 235, 205)),
    (255, 222, 173): ColorInfo("NWHT", "NavajoWhite", "#FFDEAD", (255, 222, 173)),
}

# Essential Extras (60 colors) - Skin tones, intermediate grays, etc.
RGB_EXTRA_COLORS = {
    # Skin Tones (20 variations)
    (255, 228, 196): ColorInfo("SKN1", "SkinTone1", "#FFE4C4", (255, 228, 196)),
    (250, 220, 190): ColorInfo("SKN2", "SkinTone2", "#FADCBE", (250, 220, 190)),
    (245, 210, 180): ColorInfo("SKN3", "SkinTone3", "#F5D2B4", (245, 210, 180)),
    (240, 200, 165): ColorInfo("SKN4", "SkinTone4", "#F0C8A5", (240, 200, 165)),
    (235, 190, 155): ColorInfo("SKN5", "SkinTone5", "#EBBE9B", (235, 190, 155)),
    (230, 180, 140): ColorInfo("SKN6", "SkinTone6", "#E6B48C", (230, 180, 140)),
    (222, 170, 135): ColorInfo("SKN7", "SkinTone7", "#DEAA87", (222, 170, 135)),
    (215, 160, 125): ColorInfo("SKN8", "SkinTone8", "#D7A07D", (215, 160, 125)),
    (205, 150, 115): ColorInfo("SKN9", "SkinTone9", "#CD9673", (205, 150, 115)),
    (195, 140, 105): ColorInfo("SKN10", "SkinTone10", "#C38C69", (195, 140, 105)),
    (185, 130, 95): ColorInfo("SKN11", "SkinTone11", "#B9825F", (185, 130, 95)),
    (175, 120, 85): ColorInfo("SKN12", "SkinTone12", "#AF7855", (175, 120, 85)),
    (165, 110, 75): ColorInfo("SKN13", "SkinTone13", "#A56E4B", (165, 110, 75)),
    (155, 100, 65): ColorInfo("SKN14", "SkinTone14", "#9B6441", (155, 100, 65)),
    (145, 90, 60): ColorInfo("SKN15", "SkinTone15", "#915A3C", (145, 90, 60)),
    (135, 85, 55): ColorInfo("SKN16", "SkinTone16", "#875537", (135, 85, 55)),
    (125, 75, 50): ColorInfo("SKN17", "SkinTone17", "#7D4B32", (125, 75, 50)),
    (115, 70, 45): ColorInfo("SKN18", "SkinTone18", "#73462D", (115, 70, 45)),
    (105, 65, 40): ColorInfo("SKN19", "SkinTone19", "#694128", (105, 65, 40)),
    (95, 60, 35): ColorInfo("SKN20", "SkinTone20", "#5F3C23", (95, 60, 35)),
    
    # Intermediate Grays (20 variations)
    (240, 240, 240): ColorInfo("GRY01", "Gray1", "#F0F0F0", (240, 240, 240)),
    (230, 230, 230): ColorInfo("GRY02", "Gray2", "#E6E6E6", (230, 230, 230)),
    (215, 215, 215): ColorInfo("GRY03", "Gray3", "#D7D7D7", (215, 215, 215)),
    (200, 200, 200): ColorInfo("GRY04", "Gray4", "#C8C8C8", (200, 200, 200)),
    (185, 185, 185): ColorInfo("GRY05", "Gray5", "#B9B9B9", (185, 185, 185)),
    (175, 175, 175): ColorInfo("GRY06", "Gray6", "#AFAFAF", (175, 175, 175)),
    (160, 160, 160): ColorInfo("GRY07", "Gray7", "#A0A0A0", (160, 160, 160)),
    (150, 150, 150): ColorInfo("GRY08", "Gray8", "#969696", (150, 150, 150)),
    (140, 140, 140): ColorInfo("GRY09", "Gray9", "#8C8C8C", (140, 140, 140)),
    (130, 130, 130): ColorInfo("GRY10", "Gray10", "#828282", (130, 130, 130)),
    (120, 120, 120): ColorInfo("GRY11", "Gray11", "#787878", (120, 120, 120)),
    (110, 110, 110): ColorInfo("GRY12", "Gray12", "#6E6E6E", (110, 110, 110)),
    (100, 100, 100): ColorInfo("GRY13", "Gray13", "#646464", (100, 100, 100)),
    (90, 90, 90): ColorInfo("GRY14", "Gray14", "#5A5A5A", (90, 90, 90)),
    (80, 80, 80): ColorInfo("GRY15", "Gray15", "#505050", (80, 80, 80)),
    (70, 70, 70): ColorInfo("GRY16", "Gray16", "#464646", (70, 70, 70)),
    (60, 60, 60): ColorInfo("GRY17", "Gray17", "#3C3C3C", (60, 60, 60)),
    (50, 50, 50): ColorInfo("GRY18", "Gray18", "#323232", (50, 50, 50)),
    (40, 40, 40): ColorInfo("GRY19", "Gray19", "#282828", (40, 40, 40)),
    (30, 30, 30): ColorInfo("GRY20", "Gray20", "#1E1E1E", (30, 30, 30)),
    
    # Additional useful colors (20)
    (255, 248, 220): ColorInfo("CRNK", "Cornsilk", "#FFF8DC", (255, 248, 220)),
    (220, 220, 220): ColorInfo("IVRY", "Ivory", "#FFFFF0", (220, 220, 220)),
    (255, 240, 245): ColorInfo("LBLU", "LavenderBlush", "#FFF0F5", (255, 240, 245)),
    (135, 206, 250): ColorInfo("LSKY", "LightSkyBlue", "#87CEFA", (135, 206, 250)),
    (173, 216, 230): ColorInfo("LTBL", "LightBlue", "#ADD8E6", (173, 216, 230)),
    (240, 230, 140): ColorInfo("KHKI", "Khaki", "#F0E68C", (240, 230, 140)),
    (255, 160, 122): ColorInfo("LSAL", "LightSalmon", "#FFA07A", (255, 160, 122)),
    (250, 128, 114): ColorInfo("SALM", "Salmon", "#FA8072", (250, 128, 114)),
    (255, 127, 80): ColorInfo("CORL", "Coral", "#FF7F50", (255, 127, 80)),
    (255, 99, 71): ColorInfo("TOMA", "Tomato", "#FF6347", (255, 99, 71)),
    (255, 69, 0): ColorInfo("ORED", "OrangeRed", "#FF4500", (255, 69, 0)),
    (255, 140, 0): ColorInfo("DORG", "DarkOrange", "#FF8C00", (255, 140, 0)),
    (255, 215, 0): ColorInfo("GOLD", "Gold", "#FFD700", (255, 215, 0)),
    (189, 183, 107): ColorInfo("DKHA", "DarkKhaki", "#BDB76B", (189, 183, 107)),
    (128, 128, 0): ColorInfo("OLIV", "Olive", "#808000", (128, 128, 0)),
    (85, 107, 47): ColorInfo("DOLG", "DarkOliveGreen", "#556B2F", (85, 107, 47)),
    (107, 142, 35): ColorInfo("OLGR", "OliveGreen", "#6B8E23", (107, 142, 35)),
    (154, 205, 50): ColorInfo("YGRN", "YellowGreen", "#9ACD32", (154, 205, 50)),
    (124, 252, 0): ColorInfo("LWNV", "LawnGreen", "#7CFC00", (124, 252, 0)),
    (127, 255, 0): ColorInfo("CHRT", "Chartreuse", "#7FFF00", (127, 255, 0)),
}

# Combined Universal RGB Palette
RGB_UNIVERSAL_COLORS = {**RGB_CSS_COLORS, **RGB_EXTRA_COLORS}

print(f"✅ RGB Universal Palette loaded: {len(RGB_UNIVERSAL_COLORS)} colors")
print(f"   - CSS Standard: {len(RGB_CSS_COLORS)}")
print(f"   - Essential Extras: {len(RGB_EXTRA_COLORS)}")
