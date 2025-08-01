-- [[ core/options.lua ]]

local opt = vim.opt -- dla zwięzłości

-- Wygląd
opt.number = true         -- Pokaż numery linii
opt.relativenumber = true -- Pokaż relatywne numery linii
opt.termguicolors = true  -- Lepsze kolory w terminalu
opt.signcolumn = "yes"    -- Zawsze pokazuj kolumnę na znaki (np. błędy LSP, Gitsigns)

-- Wcięcia
opt.tabstop = 2      -- Liczba spacji dla tabulatora
opt.shiftwidth = 2   -- Liczba spacji dla auto-wcięcia
opt.expandtab = true -- Używaj spacji zamiast tabulatorów
opt.autoindent = true

-- Wyszukiwanie
opt.ignorecase = true -- Ignoruj wielkość liter przy wyszukiwaniu...
opt.smartcase = true  -- ...chyba że wpisano wielką literę

-- Inne
opt.wrap = false            -- Nie zawijaj linii
opt.backup = false          -- Wyłącz tworzenie backupów
opt.swapfile = false        -- Wyłącz pliki swap
opt.undofile = true         -- Włącz historię zmian (undo) nawet po zamknięciu pliku
opt.splitright = true       -- Otwieraj pionowe splity po prawej
opt.splitbelow = true       -- Otwieraj poziome splity na dole
opt.scrolloff = 8           -- Trzymaj 8 linii kontekstu powyżej/poniżej kursora
opt.sidescrolloff = 8
opt.mouse = "a"             -- Włącz obsługę myszy
