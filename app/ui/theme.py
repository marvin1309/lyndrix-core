from nicegui import ui

class UIStyles:
    # ----------------------------------------------------
    # 1. KARTEN & CONTAINER
    # ----------------------------------------------------
    # Nutzt jetzt spezifische Klassen, die wir unten im CSS definieren
    CARD_BASE = 'p-6 rounded-3xl shadow-lg border border-slate-200 dark:border-zinc-800 lyndrix-card'
    CARD_GLASS = 'p-6 rounded-3xl shadow-lg border border-slate-200 dark:border-zinc-800 lyndrix-glass-card'
    CARD_HIGHLIGHT = 'p-6 rounded-3xl border-2 border-primary bg-indigo-50/50 dark:bg-indigo-900/20'

    # ----------------------------------------------------
    # 2. STRUKTUR & LAYOUT
    # ----------------------------------------------------
    HEADER = '!bg-white/80 dark:!bg-zinc-950/80 backdrop-blur-md border-b border-slate-200 dark:border-zinc-800 text-slate-800 dark:text-white transition-colors'
    SIDEBAR = '!bg-slate-50 dark:!bg-zinc-950 border-r border-slate-200 dark:border-zinc-800 transition-colors'
    NAV_CATEGORY = 'text-[9px] px-4 opacity-50 mt-4 text-slate-500 dark:text-zinc-400 font-bold tracking-widest uppercase'
    NAV_LINK = 'flex items-center gap-3 px-4 py-2 hover:bg-slate-200 dark:hover:bg-zinc-800 no-underline text-slate-700 dark:text-zinc-300 transition-colors w-full rounded-lg mx-2'

    # ----------------------------------------------------
    # 3. TYPOGRAFIE
    # ----------------------------------------------------
    TITLE_H1 = 'text-3xl font-bold tracking-tight text-slate-900 dark:text-white'
    TITLE_H2 = 'text-2xl font-bold tracking-tight text-slate-800 dark:text-zinc-100'
    TEXT_MUTED = 'text-sm text-slate-500 dark:text-zinc-400'
    LABEL_MINI = 'text-[10px] font-bold uppercase tracking-widest text-slate-400 dark:text-zinc-500'

    # ----------------------------------------------------
    # 4. BUTTONS
    # ----------------------------------------------------
    BUTTON_PRIMARY = 'w-full py-4 bg-primary hover:bg-opacity-80 rounded-xl font-bold transition-all text-white'
    BUTTON_SECONDARY = 'w-full py-4 bg-slate-200 dark:bg-zinc-800 hover:bg-slate-300 dark:hover:bg-zinc-700 rounded-xl font-bold transition-all text-slate-900 dark:text-white'

    # ----------------------------------------------------
    # 5. DROPDOWN MENÜS
    # ----------------------------------------------------
    MENU_CONTAINER = 'lyndrix-menu shadow-2xl rounded-2xl overflow-hidden border border-slate-200 dark:border-zinc-800'
    MENU_ITEM = 'text-slate-700 dark:text-zinc-200 hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors px-4 py-2'
    MENU_ITEM_DANGER = 'text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors px-4 py-2'


def apply_theme():
    """Wendet die globalen Systemfarben und das CSS an."""
    ui.colors(
        primary='#6366f1', secondary='#0ea5e9', accent='#8b5cf6',
        positive='#22c55e', negative='#ef4444', info='#3b82f6', warning='#f59e0b'
    )
    
    ui.dark_mode().enable()

    ui.add_head_html('''
        <style>
            body { 
                font-family: 'Inter', system-ui, sans-serif; 
                transition: background-color 0.3s ease;
            }

            /* --- DER AGGRESSIVE FIX FÜR KARTEN & MENÜS --- */
            
            /* Basis-Karten */
            .lyndrix-card {
                background-color: white !important;
            }
            .body--dark .lyndrix-card {
                background-color: #18181b !important; /* zinc-900 */
            }

            /* Glass-Karten */
            .lyndrix-glass-card {
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
            }
            .body--light .lyndrix-glass-card {
                background-color: rgba(255, 255, 255, 0.7) !important;
            }
            .body--dark .lyndrix-glass-card {
                background-color: rgba(24, 24, 27, 0.6) !important;
            }

            /* Dropdown Menüs (QMenu) */
            .q-menu.lyndrix-menu {
                background-color: white !important;
                min-width: 200px;
            }
            .body--dark .q-menu.lyndrix-menu {
                background-color: #18181b !important;
                color: #f4f4f5 !important;
            }
            
            /* Genereller Quasar Reset für Darkmode */
            .body--dark .q-card {
                background: #18181b;
                color: white;
            }

            /* Scrollbar Styling */
            ::-webkit-scrollbar { width: 8px; height: 8px; }
            ::-webkit-scrollbar-track { background: transparent; }
            body.body--dark ::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 4px; }
            body.body--light ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
        </style>
    ''')