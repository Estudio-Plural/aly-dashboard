"""Isotipo y logotipo de Aly — fuente única de la marca.

Aly es el asistente de WhatsApp de Equimundo (Apapáchar en Colombia, Semillas
de Igualdad en México y el demo). La «a» es una burbuja de chat con la semilla
adentro: la conversación (WhatsApp), el cuidado y lo que crece (Semillas); el
resto del nombre va con el mismo trazo redondo.

Para regenerar los SVG de esta carpeta:

    python3 assets/brand/generar_marca.py

Los PNG (WhatsApp 640, ícono 512, favicon 64, apple-touch 180, cabecera de
correo 600×120) se rasterizan desde estos SVG con un navegador headless; no
hace falta regenerarlos salvo que cambie el dibujo. Ver CLAUDE.md, «Marca».
"""

import math

INDIGO, GIRASOL, CREMA = "#2A2380", "#FFC83D", "#FFF9EC"
W = 11            # grosor del trazo
R = 24            # radio del ojo (interior del trazo)

def _bubble(cx, cy, ink):
    """Burbuja rellena con cola abajo a la izquierda (forma de chat)."""
    ro = R + W / 2
    a = math.radians(128)
    bx, by = cx + ro * math.cos(a), cy + ro * math.sin(a)          # donde nace la cola
    a2 = math.radians(160)
    b2x, b2y = cx + ro * math.cos(a2), cy + ro * math.sin(a2)
    tipx, tipy = cx - ro - 3.5, cy + ro + 1.5                       # punta de la cola
    return (f'<circle cx="{cx}" cy="{cy}" r="{ro}" fill="{ink}"/>'
            f'<path d="M{b2x:.2f},{b2y:.2f} Q{cx-ro+2:.2f},{cy+ro-4:.2f} {tipx:.2f},{tipy:.2f} '
            f'Q{bx-4:.2f},{by+6:.2f} {bx+6:.2f},{by+2:.2f} Z" fill="{ink}"/>')

def _a(cx, cy, ink, seed):
    sx = cx + R + W / 2 - 0.5
    return (_bubble(cx, cy, ink) +
            f'<path d="M{sx:.2f},{cy-R:.2f} L{sx:.2f},{cy+R+2:.2f}" stroke="{ink}" stroke-width="{W}" stroke-linecap="round"/>'
            f'<circle cx="{cx}" cy="{cy}" r="8" fill="{seed}"/>')

def isotipo(ink=INDIGO, seed=GIRASOL, bg=None, rx=24, size=None):
    s = f' width="{size}" height="{size}"' if size else ""
    bgs = f'<rect width="100" height="100" rx="{rx}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"{s} role="img" aria-label="Aly">'
            f'{bgs}{_a(46, 50, ink, seed)}</svg>')

def logotipo(ink=INDIGO, seed=GIRASOL, height=None):
    """«aly»: la a-burbuja + l + y del mismo trazo. viewBox 0 0 196 112 (línea base en y=83)."""
    cx, cy = 34.5, 54
    top, base = cy - R - W / 2, cy + R + W / 2          # altura x
    sa = cx + R + W / 2 - 0.5                              # asta de la a
    lx = sa + 22                                           # l
    yl, yr = lx + 22, lx + 22 + 2 * R                      # y: brazo izq y der
    ycx = (yl + yr) / 2
    parts = [_a(cx, cy, ink, seed),
             f'<path d="M{lx:.2f},{top-21:.2f} L{lx:.2f},{base-W/2:.2f}" stroke="{ink}" stroke-width="{W}" stroke-linecap="round"/>',
             # y: «u» redonda cuyo brazo derecho baja y termina en un gancho hacia la izquierda
             f'<path d="M{yl:.2f},{top+W/2:.2f} L{yl:.2f},{cy+2:.2f} A{R},{R} 0 0 0 {yr:.2f},{cy+2:.2f}" fill="none" stroke="{ink}" stroke-width="{W}" stroke-linecap="round"/>',
             f'<path d="M{yr:.2f},{top+W/2:.2f} L{yr:.2f},{base+6:.2f} Q{yr:.2f},{base+22:.2f} {ycx:.2f},{base+22:.2f} L{ycx-7:.2f},{base+22:.2f}" fill="none" stroke="{ink}" stroke-width="{W}" stroke-linecap="round" stroke-linejoin="round"/>']
    h = f' height="{height}"' if height else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {yr+W:.0f} 118"{h} role="img" aria-label="Aly">'
            + "".join(parts) + '</svg>')

if __name__ == "__main__":
    from pathlib import Path
    out = Path(__file__).resolve().parent
    piezas = {
        "aly-isotipo.svg":        isotipo(),
        "aly-isotipo-crema.svg":  isotipo(ink=CREMA),
        "aly-icono-app.svg":      isotipo(ink=CREMA, bg=INDIGO, rx=22),
        "aly-logotipo.svg":       logotipo(),
        "aly-logotipo-crema.svg": logotipo(ink=CREMA),
    }
    for nombre, svg in piezas.items():
        (out / nombre).write_text(svg)
        print("escrito", nombre)
