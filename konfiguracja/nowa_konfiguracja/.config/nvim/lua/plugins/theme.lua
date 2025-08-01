-- [[ plugins/theme.lua ]]

return {
  "folke/tokyonight.nvim",
  lazy = false, -- ładuj od razu przy starcie
  priority = 1000, -- upewnij się, że załaduje się jako pierwszy
  config = function()
    -- Ustawienie motywu
    vim.cmd.colorscheme "tokyonight"
  end,
}
