import io
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.collections import LineCollection
from shiny import App, ui, render, reactive

# ── Colour palettes ──────────────────────────────────────────────────────────
COLORMAPS = {
    "Cyan":    ["#001a33", "#00e5ff"],
    "Magenta": ["#1a001a", "#ff00ff"],
    "Green":   ["#001a00", "#39ff14"],
    "Gold":    ["#1a0d00", "#ffd700"],
    "White":   ["#111111", "#ffffff"],
}

# Accent hex used to theme the UI for each trace colour (the bright end of the
# colormap, lightly softened for white so it stays legible on the dark panel).
ACCENTS = {name: stops[1] for name, stops in COLORMAPS.items()}
ACCENTS["White"] = "#e8f0f8"


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

# ── Custom CSS ────────────────────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700&display=swap');

:root {
  --bg:        #0a0a0f;
  --panel-bg:  #0f0f18;
  --accent:    #00e5ff;
  --accent2:   #ff00ff;
  --text:      #c8d6e5;
  --text-dim:  #5a6a7a;
  --border:    #1e2a3a;
  --glow:      0 0 8px rgba(0,229,255,.45), 0 0 20px rgba(0,229,255,.15);
  --glow2:     0 0 6px rgba(255,0,255,.4);
  --radius:    8px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

html, body, .bslib-page-fillable {
  height: 100%;
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'Share Tech Mono', monospace !important;
}

/* ── Sidebar ── */
.bslib-sidebar-layout > .sidebar {
  background: var(--panel-bg) !important;
  border-right: 1px solid var(--border) !important;
  padding: 1.5rem 1.2rem !important;
  overflow-y: auto;
}

/* App title */
.app-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: var(--accent);
  text-shadow: var(--glow);
  margin-bottom: .25rem;
}
.app-subtitle {
  font-size: .72rem;
  color: var(--text-dim);
  letter-spacing: .08em;
  margin-bottom: 1.6rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: .9rem;
}

/* Section labels */
.ctrl-label {
  font-size: .65rem;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--text-dim);
  margin: 1.1rem 0 .35rem;
}

/* Sliders */
.shiny-input-container label {
  color: var(--text) !important;
  font-size: .78rem !important;
  letter-spacing: .06em;
}
.irs--shiny .irs-bar,
.irs--shiny .irs-bar--single {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
}
.irs--shiny .irs-handle {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
  box-shadow: var(--glow) !important;
}
.irs--shiny .irs-from, .irs--shiny .irs-to, .irs--shiny .irs-single {
  background: var(--panel-bg) !important;
  color: var(--accent) !important;
  font-family: 'Share Tech Mono', monospace !important;
  font-size: .72rem !important;
  border: 1px solid var(--border) !important;
  border-radius: 4px !important;
}
.irs--shiny .irs-line {
  background: var(--border) !important;
  border-color: var(--border) !important;
}

/* Selectize */
.selectize-control .selectize-input {
  background: var(--panel-bg) !important;
  color: var(--accent) !important;
  border: 1px solid var(--border) !important;
  font-family: 'Share Tech Mono', monospace !important;
  font-size: .78rem !important;
  box-shadow: none !important;
  border-radius: var(--radius) !important;
}
.selectize-control .selectize-dropdown {
  background: var(--panel-bg) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  font-family: 'Share Tech Mono', monospace !important;
  font-size: .78rem !important;
}
.selectize-dropdown .option.selected,
.selectize-dropdown .option:hover {
  background: rgba(0,229,255,.12) !important;
  color: var(--accent) !important;
}

/* ── Sweep button ── */
#sweep_toggle {
  width: 100%;
  margin-top: .4rem;
  padding: .55rem .8rem;
  background: transparent !important;
  border: 1px solid var(--accent) !important;
  color: var(--accent) !important;
  font-family: 'Orbitron', sans-serif !important;
  font-size: .72rem !important;
  font-weight: 700 !important;
  letter-spacing: .16em !important;
  text-transform: uppercase;
  border-radius: var(--radius) !important;
  cursor: pointer;
  transition: background .2s, box-shadow .2s;
}
#sweep_toggle:hover {
  background: rgba(0,229,255,.1) !important;
  box-shadow: var(--glow) !important;
}
#sweep_toggle.sweeping {
  border-color: var(--accent2) !important;
  color: var(--accent2) !important;
  background: rgba(255,0,255,.07) !important;
  box-shadow: var(--glow2) !important;
}

/* ── Download button ── */
#download_png {
  width: 100%;
  margin-top: .4rem;
  padding: .55rem .8rem;
  background: transparent !important;
  border: 1px solid var(--text-dim) !important;
  color: var(--text) !important;
  font-family: 'Orbitron', sans-serif !important;
  font-size: .72rem !important;
  font-weight: 700 !important;
  letter-spacing: .16em !important;
  text-transform: uppercase;
  border-radius: var(--radius) !important;
  cursor: pointer;
  transition: background .2s, box-shadow .2s, border-color .2s, color .2s;
}
#download_png:hover {
  border-color: var(--accent) !important;
  color: var(--accent) !important;
  background: rgba(0,229,255,.08) !important;
  box-shadow: var(--glow) !important;
}

/* Speed slider — hidden until sweep active */
#speed_row {
  overflow: hidden;
  max-height: 0;
  opacity: 0;
  transition: max-height .35s ease, opacity .3s ease;
  margin-top: .3rem;
}
#speed_row.visible {
  max-height: 90px;
  opacity: 1;
}

/* Equation badge */
.eq-badge {
  margin-top: 1.6rem;
  padding: .7rem .9rem;
  background: color-mix(in srgb, var(--accent) 6%, transparent);
  border: 1px solid color-mix(in srgb, var(--accent) 22%, transparent);
  border-radius: var(--radius);
  font-size: .72rem;
  line-height: 1.7;
  color: var(--text);
}
.eq-badge span.hi  { color: var(--accent);  text-shadow: var(--glow);  }
.eq-badge span.hi2 { color: var(--accent2); text-shadow: var(--glow2); }

/* Main panel */
.bslib-sidebar-layout > .main {
  background: var(--bg) !important;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  padding: .5rem !important;
}

/* Stats bar */
.stats-bar {
  display: flex;
  gap: 1.5rem;
  align-items: center;
  padding: .5rem 1rem .2rem;
  font-size: .7rem;
  letter-spacing: .08em;
  color: var(--text-dim);
}
.stats-bar .val { color: var(--accent); text-shadow: var(--glow); }
.sweep-pill {
  display: inline-block;
  padding: .1rem .55rem;
  border: 1px solid var(--accent2);
  border-radius: 20px;
  color: var(--accent2);
  font-size: .62rem;
  letter-spacing: .12em;
  text-shadow: var(--glow2);
  animation: pulse 1.2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: .4; }
}

/* Plot */
#plot { flex: 1; border-radius: var(--radius); overflow: hidden; }
.shiny-plot-output img { border-radius: var(--radius); }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
"""

# Small JS snippet: keeps the button style and speed slider in sync with server
# state without needing a full round-trip to re-render the button widget itself.
JS = """
Shiny.addCustomMessageHandler('sweep_state', function(sweeping) {
  var btn = document.getElementById('sweep_toggle');
  var row = document.getElementById('speed_row');
  if (sweeping) {
    btn.classList.add('sweeping');
    btn.textContent = '\\u25a0  Stop';
    row.classList.add('visible');
  } else {
    btn.classList.remove('sweeping');
    btn.textContent = '\\u25b6  Sweep \\u03b4';
    row.classList.remove('visible');
  }
});

// Retheme the UI accent to match the selected trace colour.
Shiny.addCustomMessageHandler('accent_color', function(msg) {
  var root = document.documentElement;
  root.style.setProperty('--accent', msg.accent);
  root.style.setProperty('--glow', msg.glow);
});
"""

# ── Figure builder (shared by render.plot and render.download) ───────────────
def _build_figure(a: int, b: int, delta_rad: float, n: int, color_key: str) -> plt.Figure:
    c_start, c_end = COLORMAPS[color_key]

    t = np.linspace(0, 2 * np.pi, n)
    x = np.sin(a * t + delta_rad)
    y = np.sin(b * t)

    points = np.column_stack([x, y]).reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    cmap = mcolors.LinearSegmentedColormap.from_list(
        "lissajous", [c_start, c_end, c_start], N=512
    )
    lc = LineCollection(
        segments,
        cmap=cmap,
        norm=plt.Normalize(0, 1),
        linewidth=1.4,
        alpha=0.92,
        capstyle="round",
    )
    lc.set_array(np.linspace(0, 1, len(segments)))

    fig, ax = plt.subplots(figsize=(7, 7))
    fig.patch.set_facecolor("#0a0a0f")
    ax.set_facecolor("#0a0a0f")

    ax.add_collection(lc)
    ax.set_xlim(-1.08, 1.08)
    ax.set_ylim(-1.08, 1.08)
    ax.set_aspect("equal")

    for v in np.linspace(-1, 1, 5):
        ax.axhline(v, color="#1a2030", linewidth=0.4, zorder=0)
        ax.axvline(v, color="#1a2030", linewidth=0.4, zorder=0)

    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor("#1e2a3a")
        spine.set_linewidth(0.8)

    ax.set_title(
        f"a : b  =  {a} : {b}     δ = {delta_rad:.3f} rad",
        color="#5a6a7a", fontsize=9, fontfamily="monospace", pad=10,
    )

    fig.tight_layout(pad=0.6)
    return fig


# ── UI ────────────────────────────────────────────────────────────────────────
app_ui = ui.page_fillable(
    ui.tags.style(CSS),
    ui.tags.script(JS),
    ui.layout_sidebar(
        ui.sidebar(
            ui.div(
                ui.div("Lissajous", class_="app-title"),
                ui.div("Figure Explorer", class_="app-subtitle"),
            ),

            ui.div("Frequencies", class_="ctrl-label"),
            ui.input_slider("freq_a", "a", min=1, max=10, value=3, step=1),
            ui.input_slider("freq_b", "b", min=1, max=10, value=2, step=1),

            ui.div("Phase shift δ", class_="ctrl-label"),
            ui.input_slider("delta", "δ  (× π/2)", min=0, max=4, value=1, step=0.05),

            ui.div("Sweep animation", class_="ctrl-label"),
            ui.input_action_button("sweep_toggle", "▶  Sweep δ"),
            # Speed slider always in DOM; CSS hides/shows it
            ui.div(
                ui.input_slider("sweep_speed", "Speed", min=0.005, max=0.08, value=0.025, step=0.005),
                id="speed_row",
            ),

            ui.div("Appearance", class_="ctrl-label"),
            ui.input_select(
                "color", "Trace colour",
                choices=list(COLORMAPS.keys()),
                selected="Cyan",
            ),
            ui.input_slider("resolution", "Resolution", min=500, max=10000, value=4000, step=500),

            ui.div("Export", class_="ctrl-label"),
            ui.download_button("download_png", "⬇  Save PNG"),

            ui.div(
                ui.HTML(
                    "x(t) = A · sin(<span class='hi'>a</span>·t + <span class='hi2'>δ</span>)<br>"
                    "y(t) = B · sin(<span class='hi'>b</span>·t)<br><br>"
                    "t ∈ [0, 2π]"
                ),
                class_="eq-badge",
            ),
            width="260px",
            open="desktop",
        ),

        ui.div(
            ui.div(ui.output_ui("stats"), class_="stats-bar"),
            ui.output_plot("plot", height="100%"),
            style="display:flex; flex-direction:column; height:100%; gap:.3rem;",
        ),
    ),
    fillable_mobile=True,
    title="Lissajous Explorer",
)


# ── Server ────────────────────────────────────────────────────────────────────
def server(input, output, session):
    is_sweeping = reactive.Value(False)
    sweep_delta = reactive.Value(1.0)   # tracks animated δ (0–4 range)

    # ── Toggle sweep on button press ─────────────────────────────────────────
    @reactive.effect
    @reactive.event(input.sweep_toggle)
    async def _toggle():
        sweeping = not is_sweeping.get()
        if sweeping:
            # Sync animated δ to wherever the manual slider currently sits
            with reactive.isolate():
                sweep_delta.set(float(input.delta()))
        is_sweeping.set(sweeping)
        # Push button/speed-row state to JS without re-rendering the widget
        await session.send_custom_message("sweep_state", sweeping)

    # ── Animation ticker ─────────────────────────────────────────────────────
    # IMPORTANT: all reads inside the effect are isolated so that
    # sweep_delta.set() does NOT re-trigger this effect directly.
    # Only is_sweeping and the invalidate_later timer drive re-execution.
    @reactive.effect
    def _tick():
        if not is_sweeping.get():
            return
        reactive.invalidate_later(0.04)          # schedule next frame (~25 fps)
        with reactive.isolate():
            speed = input.sweep_speed()
            new_val = (sweep_delta.get() + speed) % 4.0
            sweep_delta.set(new_val)

    # ── Retheme UI accent to match the selected trace colour ─────────────────
    @reactive.effect
    async def _sync_accent():
        hex_color = ACCENTS[input.color()]
        r, g, b = _hex_to_rgb(hex_color)
        glow = f"0 0 8px rgba({r},{g},{b},.45), 0 0 20px rgba({r},{g},{b},.15)"
        await session.send_custom_message("accent_color", {"accent": hex_color, "glow": glow})

    # ── Resolved δ ───────────────────────────────────────────────────────────
    @reactive.calc
    def current_delta_raw():
        """δ in the 0–4 range (units of π/2)."""
        if is_sweeping.get():
            return sweep_delta.get()
        return float(input.delta())

    # ── Stats bar ─────────────────────────────────────────────────────────────
    @render.ui
    def stats():
        a = input.freq_a()
        b = input.freq_b()
        delta_val = current_delta_raw() * (np.pi / 2)
        pill = "<span class='sweep-pill'>SWEEP</span>&ensp;" if is_sweeping.get() else ""
        return ui.HTML(
            f"{pill}"
            f"<span>a&thinsp;:&thinsp;b</span>&ensp;<span class='val'>{a}:{b}</span>"
            f"&emsp;<span>δ</span>&ensp;<span class='val'>{delta_val:.3f} rad</span>"
            f"&emsp;<span>pts</span>&ensp;<span class='val'>{input.resolution():,}</span>"
        )

    # ── Plot ──────────────────────────────────────────────────────────────────
    @render.plot(alt="Lissajous figure")
    def plot():
        return _build_figure(
            input.freq_a(),
            input.freq_b(),
            current_delta_raw() * (np.pi / 2),
            input.resolution(),
            input.color(),
        )

    # ── Download current frame as PNG ────────────────────────────────────────
    def _png_filename() -> str:
        a = input.freq_a()
        b = input.freq_b()
        d = current_delta_raw()
        return f"lissajous_a{a}_b{b}_d{d:.2f}.png"

    @render.download(filename=_png_filename)
    def download_png():
        fig = _build_figure(
            input.freq_a(),
            input.freq_b(),
            current_delta_raw() * (np.pi / 2),
            input.resolution(),
            input.color(),
        )
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format="png",
            dpi=200,
            facecolor=fig.get_facecolor(),
            bbox_inches="tight",
        )
        plt.close(fig)
        buf.seek(0)
        yield buf.read()


app = App(app_ui, server)
