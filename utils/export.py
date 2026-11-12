"""Exportación sin identificar (Excel) para M&E.

Pedido de Rachel para Semillas (2026-11-11): un export con ID seudónimo,
fecha/hora y alerta de riesgo, sin número ni nombre, para que el equipo de M&E
calcule sus propias cifras (registradas, las que vuelven, activas por semana,
% respondidas con el material).

Hojas: «Cómo leer», «Mensajes», «Conversaciones», «Registros». No lleva
teléfono, nombre, texto de mensajes, resúmenes ni ``flag_reasoning`` (texto
libre). Los datos crudos salen de ``db.get_pseudonymous_export_data``; acá se
reemplazan los identificadores y, antes de devolver el archivo, se revisa que
ningún número ni ``conversation_id`` crudo haya quedado en una celda.
"""

from __future__ import annotations

import datetime
import io
import re
from typing import Dict, List, Optional

import pandas as pd
from zoneinfo import ZoneInfo

from utils import pseudonym
from utils.bots import bot_weekly_deidentified

_LOCAL_TZ = ZoneInfo("America/Bogota")

_RISK_TOKEN_RE = re.compile(r"^(HIGH|MEDIUM|LOW)-(.+)$", re.IGNORECASE)

L = {
    "es": {
        "sheet_readme": "Cómo leer", "sheet_msgs": "Mensajes",
        "sheet_convs": "Conversaciones", "sheet_regs": "Registros",
        "id": "ID", "conv": "ID conversación", "ts": "Fecha y hora",
        "week": "Semana (lunes)", "kind": "Tipo", "reply": "Respuesta de Aly",
        "n_msgs": "Mensajes", "risk": "Alerta de riesgo", "risk_type": "Tipo de alerta",
        "reg_ts": "Fecha de registro",
        "question": "Pregunta", "social": "Saludo o cierre",
        "answered": "Con el material", "no_info": "No tengo esa información",
        "no_reply": "Sin respuesta registrada",
        "sev": {"HIGH": "Alta", "MEDIUM": "Media", "LOW": "Baja"}, "sev_none": "Ninguna",
        "title": "Aly · {program} — exportación sin identificar",
        "period": "Período", "period_val": "{a} a {b}",
        "generated": "Generado", "rows": "Filas",
        "rows_val": "{m} mensajes · {c} conversaciones · {r} registros",
        "readme": [
            ("Hora", "Todas las fechas y horas están en hora de Colombia (GMT-5), la misma que usan el "
                     "dashboard y el reporte de los lunes.{mx_time}"),
            ("ID", "Seudónimo de cada persona (D-…). No es el teléfono y no se puede convertir en él. "
                   "Es el mismo {same_in}, así que se puede "
                   "seguir a una persona en el tiempo sin saber quién es."),
            ("ID conversación", "Seudónimo de cada conversación (C-…), para unir Mensajes con Conversaciones."),
            ("Hoja Mensajes", "Un mensaje enviado por la persona por fila. No incluye las respuestas de Aly "
                              "ni el texto de ningún mensaje."),
            ("Semana (lunes)", "Lunes de la semana del mensaje (semanas de lunes a domingo), como en la "
                               "gráfica de usuarios activos por semana del dashboard."),
            ("Tipo", "«Pregunta», o «Saludo o cierre» si el mensaje es solo hola, gracias, ok, adiós o la "
                     "respuesta al aviso de privacidad. Solo las preguntas cuentan para el % de respondidas."),
            ("Respuesta de Aly", "Solo en preguntas. «No tengo esa información» si la respuesta de Aly abre con "
                                 "esa frase; «Con el material» si respondió otra cosa; «Sin respuesta registrada» "
                                 "si después no hay respuesta de Aly."),
            ("Hoja Conversaciones", "Una conversación cerrada por fila, con su fecha de cierre y cuántos mensajes tuvo."),
            ("Alerta de riesgo", "Alta, Media, Baja o Ninguna, según la clasificación que hace Aly al cerrar la "
                                 "conversación. Las alertas Alta y Media son las que llegan por correo para seguimiento."),
            ("Tipo de alerta", "Categorías de riesgo detectadas, en inglés, como las escribe Aly."),
            ("Hoja Registros", "Una persona por fila con la fecha en que se registró{reg_note}. Es acumulado: "
                               "incluye a todas las personas registradas hasta el cierre del período, aunque se "
                               "hayan registrado antes."),
            ("Ojo", "Puede haber IDs en Mensajes que no aparecen en Registros: personas que escribieron sin "
                    "completar el registro."),
            ("No incluye", "Teléfono, nombre, texto de los mensajes, resúmenes de conversación ni cuentas de prueba."),
        ],
        "reg_note_mexico": " (en México, cuando aceptó el aviso de privacidad)",
        "mx_time": " La hora del centro de México es una hora menos.",
        "same_in": ("en todas las hojas y en todas las exportaciones",
                    "en todas las hojas, en todas las exportaciones y en el Excel de los lunes"),
        "file": "aly_{bot}_sin_identificar_{a}_{b}.xlsx",
    },
    "en": {
        "sheet_readme": "How to read", "sheet_msgs": "Messages",
        "sheet_convs": "Conversations", "sheet_regs": "Registrations",
        "id": "ID", "conv": "Conversation ID", "ts": "Date and time",
        "week": "Week (Monday)", "kind": "Type", "reply": "Aly's reply",
        "n_msgs": "Messages", "risk": "Risk flag", "risk_type": "Risk type",
        "reg_ts": "Registration date",
        "question": "Question", "social": "Greeting or closing",
        "answered": "From the material", "no_info": "I don't have that information",
        "no_reply": "No reply recorded",
        "sev": {"HIGH": "High", "MEDIUM": "Medium", "LOW": "Low"}, "sev_none": "None",
        "title": "Aly · {program} — de-identified export",
        "period": "Period", "period_val": "{a} to {b}",
        "generated": "Generated", "rows": "Rows",
        "rows_val": "{m} messages · {c} conversations · {r} registrations",
        "readme": [
            ("Time", "All dates and times are in Colombia time (GMT-5), the same the dashboard and the Monday "
                     "report use.{mx_time}"),
            ("ID", "Pseudonym for each person (D-…). It is not the phone number and cannot be turned back into it. "
                   "It is the same {same_in}, so a person can be followed over "
                   "time without knowing who they are."),
            ("Conversation ID", "Pseudonym for each conversation (C-…), to join Messages with Conversations."),
            ("Messages sheet", "One message sent by the person per row. Aly's replies and message text are not included."),
            ("Week (Monday)", "Monday of the message's week (weeks run Monday to Sunday), as in the dashboard's "
                              "weekly active users chart."),
            ("Type", "«Question», or «Greeting or closing» if the message is only hello, thanks, ok, bye or the "
                     "reply to the privacy notice. Only questions count toward the answered share."),
            ("Aly's reply", "Questions only. «I don't have that information» if Aly's reply opens with that phrase; "
                            "«From the material» if it answered anything else; «No reply recorded» if no reply "
                            "from Aly follows."),
            ("Conversations sheet", "One closed conversation per row, with its closing date and message count."),
            ("Risk flag", "High, Medium, Low or None, from the classification Aly makes when it closes the "
                          "conversation. High and Medium are the ones sent by email for case follow-up."),
            ("Risk type", "Risk categories detected, as Aly writes them."),
            ("Registrations sheet", "One person per row with the date they registered{reg_note}. It is "
                                    "cumulative: it includes everyone registered by the end of the period, even "
                                    "if they registered earlier."),
            ("Note", "Some IDs in Messages may not appear in Registrations: people who wrote without completing "
                     "registration."),
            ("Not included", "Phone number, name, message text, conversation summaries or test accounts."),
        ],
        "reg_note_mexico": " (in Mexico, when they accepted the privacy notice)",
        "mx_time": " Central Mexico time is one hour earlier.",
        "same_in": ("across sheets and across exports",
                    "across sheets, across exports and in the Monday Excel"),
        "file": "aly_{bot}_deidentified_{a}_{b}.xlsx",
    },
}


def file_name(bot_id: str, date_from: str, date_to_incl: str, lang: str) -> str:
    return L[_lang(lang)]["file"].format(bot=bot_id, a=date_from, b=date_to_incl)


def _lang(lang: Optional[str]) -> str:
    return lang if lang in L else "es"


def _risk_types(flags) -> str:
    out: List[str] = []
    for tok in str(flags or "").split(","):
        m = _RISK_TOKEN_RE.match(tok.strip())
        if m and m.group(2) not in out:
            out.append(m.group(2))
    return ", ".join(out)


def _week_monday(ts) -> Optional[datetime.date]:
    if pd.isna(ts):
        return None
    d = pd.Timestamp(ts).date()
    return d - datetime.timedelta(days=d.weekday())


def _assert_deidentified(frames: Dict[str, pd.DataFrame], raw: Dict[str, pd.DataFrame]) -> None:
    """Falla si algún número o ``conversation_id`` crudo quedó en una celda.

    Igualdad exacta para todos; búsqueda como subcadena solo para los de 10+
    caracteres (teléfonos), para no confundir un id corto con un pedazo de hex.
    """
    idents = set()
    for df in raw.values():
        for col in ("client_number", "conversation_id"):
            if col in df.columns:
                idents.update(str(v) for v in df[col].dropna().unique() if str(v).strip())
    if not idents:
        return
    long_ids = sorted((i for i in idents if len(i) >= 10), key=len, reverse=True)
    long_re = re.compile("|".join(re.escape(i) for i in long_ids)) if long_ids else None
    for name, df in frames.items():
        for col in df.columns:
            for val in df[col].dropna().astype(str):
                if val in idents or (long_re is not None and long_re.search(val)):
                    raise RuntimeError(f"Identificador crudo en la hoja «{name}», columna «{col}»")


def _style(ws, widths: List[int], date_cols=(), datetime_cols=()) -> None:
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    header_fill = PatternFill("solid", fgColor="110079")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(vertical="center")
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for idx in datetime_cols:
        for row in ws.iter_rows(min_row=2, min_col=idx, max_col=idx):
            row[0].number_format = "yyyy-mm-dd hh:mm"
    for idx in date_cols:
        for row in ws.iter_rows(min_row=2, min_col=idx, max_col=idx):
            row[0].number_format = "yyyy-mm-dd"
    ws.freeze_panes = "A2"
    if ws.max_row > 1:
        ws.auto_filter.ref = ws.dimensions


def build_excel(
    raw: Dict[str, pd.DataFrame],
    key: bytes,
    *,
    bot_id: str,
    program: str,
    date_from: str,
    date_to_incl: str,
    lang: str = "es",
    generated_at: Optional[datetime.datetime] = None,
) -> bytes:
    """Arma el .xlsx sin identificar a partir de ``db.get_pseudonymous_export_data``."""
    lx = L[_lang(lang)]
    uid = lambda n: pseudonym.user_id(key, n)  # noqa: E731
    cid = lambda n, c: pseudonym.conversation_id(key, n, c)  # noqa: E731

    msgs_raw = raw.get("messages", pd.DataFrame())
    convs_raw = raw.get("conversations", pd.DataFrame())
    regs_raw = raw.get("registrations", pd.DataFrame())

    def _reply(r) -> str:
        if r["social"]:
            return ""
        if r["no_info"]:
            return lx["no_info"]
        return lx["answered"] if r["has_reply"] else lx["no_reply"]

    msg_cols = [lx["id"], lx["conv"], lx["ts"], lx["week"], lx["kind"], lx["reply"]]
    if msgs_raw.empty:
        msgs = pd.DataFrame(columns=msg_cols)
    else:
        m = msgs_raw.copy()
        m["social"] = m["social"].fillna(False).astype(bool)
        m["no_info"] = m["no_info"].fillna(False).astype(bool)
        m["has_reply"] = m["has_reply"].fillna(False).astype(bool)
        msgs = pd.DataFrame({
            lx["id"]: [uid(n) for n in m["client_number"]],
            lx["conv"]: [cid(n, c) for n, c in zip(m["client_number"], m["conversation_id"])],
            lx["ts"]: pd.to_datetime(m["local_ts"]),
            lx["week"]: [_week_monday(t) for t in m["local_ts"]],
            lx["kind"]: [lx["social"] if s else lx["question"] for s in m["social"]],
            lx["reply"]: [_reply(r) for _, r in m.iterrows()],
        })

    conv_cols = [lx["id"], lx["conv"], lx["ts"], lx["n_msgs"], lx["risk"], lx["risk_type"]]
    if convs_raw.empty:
        convs = pd.DataFrame(columns=conv_cols)
    else:
        c = convs_raw
        sev = [str(s or "").strip().upper() for s in c["flag_severity"]]
        convs = pd.DataFrame({
            lx["id"]: [uid(n) for n in c["client_number"]],
            lx["conv"]: [cid(n, x) for n, x in zip(c["client_number"], c["conversation_id"])],
            lx["ts"]: pd.to_datetime(c["local_ts"]),
            lx["n_msgs"]: pd.to_numeric(c["messages_count"], errors="coerce").astype("Int64"),
            lx["risk"]: [lx["sev"].get(s, lx["sev_none"]) for s in sev],
            lx["risk_type"]: [_risk_types(f) if s in lx["sev"] else "" for f, s in zip(c["flags"], sev)],
        })

    reg_cols = [lx["id"], lx["reg_ts"]]
    if regs_raw.empty:
        regs = pd.DataFrame(columns=reg_cols)
    else:
        regs = pd.DataFrame({
            lx["id"]: [uid(n) for n in regs_raw["client_number"]],
            lx["reg_ts"]: pd.to_datetime(regs_raw["local_ts"]),
        })

    generated_at = generated_at or datetime.datetime.now(_LOCAL_TZ)
    is_mx = bot_id == "mexico"
    fill = {
        "reg_note": lx["reg_note_mexico"] if is_mx else "",
        "mx_time": lx["mx_time"] if is_mx else "",
        # Solo si el Excel de los lunes de ese bot también va sin identificar.
        "same_in": lx["same_in"][1 if bot_weekly_deidentified(bot_id) else 0],
    }
    readme_rows = [
        (lx["period"], lx["period_val"].format(a=date_from, b=date_to_incl)),
        (lx["generated"], generated_at.strftime("%Y-%m-%d %H:%M") + " (GMT-5)"),
        (lx["rows"], lx["rows_val"].format(m=len(msgs), c=len(convs), r=len(regs))),
        ("", ""),
    ] + [(k, v.format(**fill)) for k, v in lx["readme"]]
    readme = pd.DataFrame(readme_rows, columns=[lx["title"].format(program=program), ""])

    frames = {lx["sheet_msgs"]: msgs, lx["sheet_convs"]: convs, lx["sheet_regs"]: regs}
    _assert_deidentified({lx["sheet_readme"]: readme, **frames}, raw)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        readme.to_excel(writer, index=False, sheet_name=lx["sheet_readme"])
        msgs.to_excel(writer, index=False, sheet_name=lx["sheet_msgs"])
        convs.to_excel(writer, index=False, sheet_name=lx["sheet_convs"])
        regs.to_excel(writer, index=False, sheet_name=lx["sheet_regs"])

        from openpyxl.styles import Alignment, Font
        ws = writer.sheets[lx["sheet_readme"]]
        ws.column_dimensions["A"].width = 24
        ws.column_dimensions["B"].width = 110
        ws["A1"].font = Font(bold=True, size=13)
        for row in ws.iter_rows(min_row=2):
            row[0].font = Font(bold=True)
            row[1].alignment = Alignment(wrap_text=True, vertical="top")
            row[0].alignment = Alignment(vertical="top")

        _style(writer.sheets[lx["sheet_msgs"]], [13, 17, 18, 15, 18, 28], date_cols=(4,), datetime_cols=(3,))
        _style(writer.sheets[lx["sheet_convs"]], [13, 17, 18, 11, 16, 40], datetime_cols=(3,))
        _style(writer.sheets[lx["sheet_regs"]], [13, 20], datetime_cols=(2,))
    return buf.getvalue()
