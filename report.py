"""
TerraAudit — PDF звіт
Генерує завантажуваний звіт по ділянці.
Використовує DejaVuSans для підтримки кирилиці.
"""

from fpdf import FPDF
import pandas as pd
from datetime import datetime
import os
import matplotlib


# ─────────────────────────────────────────────
# Шрифт із підтримкою кирилиці
# Використовуємо DejaVu з пакету matplotlib — нічого не завантажується
# ─────────────────────────────────────────────

def _get_font_paths() -> tuple:
    _font_dir = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
    regular = os.path.join(_font_dir, "DejaVuSans.ttf")
    bold    = os.path.join(_font_dir, "DejaVuSans-Bold.ttf")
    if not os.path.exists(bold):
        bold = regular
    return regular, bold

FONT_PATH, FONT_BOLD_PATH = _get_font_paths()

def _ensure_fonts():
    """Нічого не робить — шрифти вже є в matplotlib."""
    pass


# ─────────────────────────────────────────────
# PDF клас
# ─────────────────────────────────────────────

class TerraAuditReport(FPDF):

    def header(self):
        self.set_font("DejaVu", "B", 13)
        self.set_fill_color(26, 52, 97)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, "  TerraAudit | Супутниковий Аудит Громад", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(3)

    def footer(self):
        self.set_y(-12)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(
            0, 8,
            f"Згенеровано TerraAudit | {datetime.now().strftime('%d.%m.%Y %H:%M')} | Потребує верифікації",
            align="C",
        )

    def section_title(self, title: str):
        self.set_font("DejaVu", "B", 11)
        self.set_fill_color(240, 244, 255)
        self.set_text_color(26, 52, 97)
        self.cell(0, 8, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def kv_row(self, key: str, value: str, highlight: bool = False):
        if highlight:
            self.set_fill_color(255, 243, 205)
            self.set_font("DejaVu", "", 10)
            self.cell(70, 7, f"  {key}", fill=True)
            self.set_font("DejaVu", "B", 10)
            self.cell(0, 7, f"  {value}", fill=True, new_x="LMARGIN", new_y="NEXT")
        else:
            self.set_fill_color(250, 250, 250)
            self.set_font("DejaVu", "", 10)
            self.cell(70, 7, f"  {key}", fill=True, border="B")
            self.cell(0, 7, f"  {value}", border="B", new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def score_block(self, score: float, label: str, color_rgb: tuple):
        r, g, b = color_rgb
        self.set_fill_color(r, g, b)
        self.set_text_color(255, 255, 255)
        self.set_font("DejaVu", "B", 26)
        self.cell(38, 18, f"{score:.1f}", fill=True, align="C")
        self.set_font("DejaVu", "B", 13)
        self.cell(0, 18, f"  / 10  —  {label}", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(3)

    def _clean(self, text: str) -> str:
        """Прибирає markdown-символи для PDF."""
        return (
            str(text)
            .replace("##", "").replace("###", "")
            .replace("**", "").replace("*", "")
            .replace("---", "─" * 40)
            .replace("🚨", "[!]").replace("⚠️", "[?]")
            .replace("✅", "[OK]").replace("📋", "")
            .replace("🛰️", "").replace("📐", "")
            .replace("🏫", "").replace("🛣️", "")
            .replace("🏥", "").strip()
        )

    def comparison_table(self, df: pd.DataFrame):
        col_widths = [52, 48, 52, 28]
        headers = df.columns.tolist()

        self.set_font("DejaVu", "B", 8)
        self.set_fill_color(26, 52, 97)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, f" {self._clean(h)}", fill=True, border=1)
        self.ln()
        self.set_text_color(0, 0, 0)

        for _, row in df.iterrows():
            self.set_font("DejaVu", "", 8)
            for i, val in enumerate(row):
                s = str(val)
                bg = (255, 255, 255)
                if "[!]" in self._clean(s) or "🚨" in s:
                    bg = (255, 220, 220)
                elif "[?]" in self._clean(s) or "⚠️" in s:
                    bg = (255, 243, 205)
                elif "[OK]" in self._clean(s) or "✅" in s:
                    bg = (220, 255, 220)
                self.set_fill_color(*bg)
                self.cell(col_widths[i], 6, f" {self._clean(s)}", fill=True, border=1)
            self.ln()
        self.ln(3)

    def prozorro_table(self, df: pd.DataFrame):
        if df is None or len(df) == 0:
            self.set_font("DejaVu", "", 9)
            self.cell(0, 7, "  Дані Прозорро недоступні", new_x="LMARGIN", new_y="NEXT")
            return

        show = df.head(8)[["title", "area_ha", "price_per_ha", "date"]].copy()
        show.columns = ["Назва лоту", "Га", "Ціна/га/рік", "Дата"]
        col_widths = [95, 20, 38, 27]

        self.set_font("DejaVu", "B", 8)
        self.set_fill_color(26, 52, 97)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(show.columns):
            self.cell(col_widths[i], 7, f" {h}", fill=True, border=1)
        self.ln()
        self.set_text_color(0, 0, 0)

        for _, row in show.iterrows():
            self.set_font("DejaVu", "", 8)
            self.set_fill_color(250, 250, 250)
            title = str(row["Назва лоту"])[:45]
            vals = [title, f"{row['Га']:.1f}", f"{row['Ціна/га/рік']:,.0f}", str(row["Дата"])]
            for i, v in enumerate(vals):
                self.cell(col_widths[i], 6, f" {v}", fill=True, border=1)
            self.ln()
        self.ln(3)


# ─────────────────────────────────────────────
# Головна функція
# ─────────────────────────────────────────────

def generate_pdf(
    address, area_ha, land_type, sat_data,
    asset_score, comparison_df,
    min_p, median_p, max_p,
    budget_result,
    teaser_text=None,
    prozorro_df=None,
) -> bytes:

    _ensure_fonts()

    pdf = TerraAuditReport()
    pdf.add_font("DejaVu",  "",  FONT_PATH)
    pdf.add_font("DejaVu",  "B", FONT_BOLD_PATH)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # 1. Загальна інформація
    pdf.section_title("1. Загальна інформація")
    pdf.kv_row("Локація:", address)
    pdf.kv_row("Площа:", f"{area_ha} га")
    pdf.kv_row("Кадастровий тип:", land_type)
    pdf.kv_row("Дата аналізу:", datetime.now().strftime("%d.%m.%Y"))
    pdf.kv_row("Режим даних:", sat_data.get("source", "Demo"))
    pdf.ln(3)

    # 2. Asset Score
    pdf.section_title("2. Індекс потенціалу монетизації (Asset Score)")
    color_map = {
        "#e74c3c": (231, 76, 60),
        "#e67e22": (230, 126, 34),
        "#f1c40f": (241, 196, 15),
        "#27ae60": (39, 174, 96),
    }
    rgb = color_map.get(asset_score.color, (100, 100, 100))
    pdf.score_block(asset_score.score, asset_score.label, rgb)

    pdf.set_font("DejaVu", "", 10)
    pdf.multi_cell(0, 6, f"  {asset_score.summary}")
    pdf.ln(3)

    pdf.set_font("DejaVu", "B", 9)
    pdf.cell(0, 6, "  Деталізація:", new_x="LMARGIN", new_y="NEXT")
    for comp, (val, desc) in asset_score.breakdown.items():
        pdf.set_font("DejaVu", "", 9)
        pdf.cell(10, 6, "")
        pdf.cell(75, 6, comp)
        pdf.set_font("DejaVu", "B", 9)
        pdf.cell(15, 6, f"{val:.1f} б.")
        pdf.set_font("DejaVu", "", 9)
        pdf.cell(0, 6, desc, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # 3. Супутникові дані
    pdf.section_title("3. Результати супутникового аналізу")
    pdf.kv_row("NDVI (рослинність):", f"{sat_data.get('ndvi_score', 0):.3f}")
    pdf.kv_row("NDBI (забудованість):", f"{sat_data.get('ndbi_score', 0):.3f}")
    pdf.kv_row(
        "VIIRS (нічна активність):",
        f"{sat_data.get('night_light_rad', 0):.2f} нВт/см2/ср",
        highlight=sat_data.get("night_light_rad", 0) > 2.0,
    )
    pdf.kv_row(
        "SAR (Sentinel-1):",
        "Зміну виявлено" if sat_data.get("sar_detected_changes") else "Стабільна поверхня",
        highlight=sat_data.get("sar_detected_changes", False),
    )
    pdf.ln(3)

    # 4. Порівняльна таблиця
    pdf.section_title("4. Порівняння: Кадастр vs Супутник")
    pdf.comparison_table(comparison_df)

    # 5. Ціновий коридор
    pdf.section_title("5. Ціновий коридор (Прозорро.Продажі)")
    pdf.kv_row("Мінімум (P25):", f"{min_p:,.0f} грн/рік")
    pdf.kv_row("Медіана:", f"{median_p:,.0f} грн/рік")
    pdf.kv_row("Максимум (P85):", f"{max_p:,.0f} грн/рік")
    pdf.ln(3)

    # 6. Прозорро лоти
    if prozorro_df is not None and len(prozorro_df) > 0:
        pdf.section_title("6. Порівняльні угоди Прозорро.Продажі")
        pdf.prozorro_table(prozorro_df)

    # 7. Бюджет
    pdf.section_title("7. Оптимальний розподіл бюджету громади")
    pdf.kv_row("Школи:", f"{budget_result.get('Школи (грн)', 0):,.0f} грн")
    pdf.kv_row("Дороги:", f"{budget_result.get('Дороги (грн)', 0):,.0f} грн")
    pdf.kv_row("Медицина:", f"{budget_result.get('Медицина (грн)', 0):,.0f} грн")
    pdf.ln(3)

    # 8. Тізер
    if teaser_text:
        pdf.add_page()
        pdf.section_title("8. Інвестиційний тізер (згенеровано ШІ)")
        pdf.set_font("DejaVu", "", 9)
        clean = pdf._clean(teaser_text)
        pdf.multi_cell(0, 5, clean)

    return bytes(pdf.output())