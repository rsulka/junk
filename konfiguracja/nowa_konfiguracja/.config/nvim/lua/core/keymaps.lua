-- [[ core/keymaps.lua ]]

-- Ustawienie klawisza <Leader> na spację
-- Musi być zdefiniowane PRZED pierwszym użyciem
vim.g.mapleader = " "
vim.g.maplocalleader = " "

local keymap = vim.keymap -- dla zwięzłości

-- Tryb Normal
-- Lepsze poruszanie się po oknach
keymap.set("n", "<C-h>", "<C-w>h", { desc = "Przełącz okno w lewo" })
keymap.set("n", "<C-l>", "<C-w>l", { desc = "Przełącz okno w prawo" })
keymap.set("n", "<C-j>", "<C-w>j", { desc = "Przełącz okno w dół" })
keymap.set("n", "<C-k>", "<C-w>k", { desc = "Przełącz okno w górę" })

-- Zmiana rozmiaru okien
keymap.set("n", "<C-Up>", ":resize -2<CR>", { desc = "Zmniejsz okno w pionie" })
keymap.set("n", "<C-Down>", ":resize +2<CR>", { desc = "Zwiększ okno w pionie" })
keymap.set("n", "<C-Left>", ":vertical resize -2<CR>", { desc = "Zmniejsz okno w poziomie" })
keymap.set("n", "<C-Right>", ":vertical resize +2<CR>", { desc = "Zwiększ okno w poziomie" })

-- Tryb Insert
-- Szybkie wyjście do trybu Normal
keymap.set("i", "jk", "<ESC>", { desc = "Wyjdź z trybu Insert" })

-- Tryb Visual
-- Przesuwanie zaznaczonych linii
keymap.set("v", "J", ":m '>+1<CR>gv=gv", { desc = "Przesuń linię w dół" })
keymap.set("v", "K", ":m '<-2<CR>gv=gv", { desc = "Przesuń linię w górę" })

-- Kopiowanie do schowka systemowego
keymap.set({ "n", "v" }, "<leader>y", [["+y]], { desc = "Kopiuj do schowka systemowego" })
keymap.set("n", "<leader>Y", [["+Y]], { desc = "Kopiuj całą linię do schowka systemowego" })

-- Wyłączanie podświetlenia wyszukiwania
keymap.set("n", "<leader>nh", ":nohl<CR>", { desc = "Wyłącz podświetlenie wyszukiwania" })
