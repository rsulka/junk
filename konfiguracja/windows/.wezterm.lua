-- wezterm-config.lua
local wezterm = require 'wezterm'

local config = {}
if wezterm.config_builder then
  config = wezterm.config_builder()
end

-- =======================================================
-- 1. Ustawienia Domyślne
-- =======================================================
-- Domyślna powłoka startowa: WSL Ubuntu (zmień na swoją dystrybucję z "wsl -l")
config.default_prog = { 'wsl.exe', '-d', 'Ubuntu' }

-- =======================================================
-- 1a. Ustawienie katalogu startowego dla domyślnej dystrybucji WSL
-- =======================================================
local wsl_domains = wezterm.default_wsl_domains()
-- Ustaw "default_cwd" na katalog domowy ~ tylko dla dystrybucji Ubuntu
for _, domain in ipairs(wsl_domains) do
  if domain.name == 'WSL:Ubuntu' then  -- Dostosuj nazwę, jeśli Twoja dystrybucja ma inną
    domain.default_cwd = "~"
  end
end
config.wsl_domains = wsl_domains
config.default_domain = 'WSL:Ubuntu'

-- =======================================================
-- 2. Menu Uruchamiania (Launcher)
-- =======================================================
config.launch_menu = {
  {
    label = 'PowerShell',
    args = { 'pwsh.exe', '-NoLogo' },
    domain = { DomainName = 'local' },
  },
}

-- Dodaj do menu wszystkie dystrybucje WSL automatycznie
for _, domain in ipairs(wsl_domains) do
  table.insert(config.launch_menu, {
    label = domain.name .. ' (WSL)',
    args = { 'wsl.exe', '-d', domain.distribution },
  })
end

-- =======================================================
-- 3. Skróty Klawiszowe
-- =======================================================
config.keys = {
  -- Launcher
  {
    key = 'L',
    mods = 'CTRL|SHIFT',
    action = wezterm.action.ShowLauncher,
  },

  -- Kopiowanie i wklejanie
  { key = 'C', mods = 'CTRL|SHIFT', action = wezterm.action.CopyTo 'Clipboard' },
  { key = 'V', mods = 'CTRL|SHIFT', action = wezterm.action.PasteFrom 'Clipboard' },  
  -- Nawigacja między kartami
  { key = 'Tab', mods = 'CTRL', action = wezterm.action.ActivateTabRelative(1) },
  { key = 'Tab', mods = 'CTRL|SHIFT', action = wezterm.action.ActivateTabRelative(-1) },
}

-- =======================================================
-- 4. Ustawienia Wyglądu (Nowoczesny wygląd)
-- =======================================================
config.color_scheme = 'Catppuccin Mocha'

-- Czcionka z ligaturami
config.font = wezterm.font({
  family = 'JetBrains Mono',
  weight = 'Regular',
  harfbuzz_features = {'calt=1', 'clig=1', 'liga=1'}
})
config.font_size = 10.0


config.window_background_opacity = 0.90

-- Ukrywanie paska kart i marginesy
config.hide_tab_bar_if_only_one_tab = true
config.window_padding = {
  left = 10,
  right = 10,
  top = 5,
  bottom = 5,
}

-- =======================================================
-- 5. Inne ustawienia
-- =======================================================
-- Nie pytaj o potwierdzenie zamknięcia okna
config.window_close_confirmation = 'NeverPrompt'

-- Rozmiar początkowy okna (w znakach)
config.initial_rows = 40
config.initial_cols = 180

return config
