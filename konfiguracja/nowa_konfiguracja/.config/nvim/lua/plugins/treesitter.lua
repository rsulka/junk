-- [[ plugins/treesitter.lua ]]

return {
  "nvim-treesitter/nvim-treesitter",
  build = ":TSUpdate", -- Komenda do instalacji/aktualizacji parserów
  config = function()
    require("nvim-treesitter.configs").setup({
      -- Lista parserów do zainstalowania.
      -- Dodaj języki, z którymi pracujesz, np. "python", "rust", "go"
      ensure_installed = { "c", "lua", "vim", "vimdoc", "javascript", "typescript", "html", "css", "python", "bash" },

      -- Włącz podświetlanie składni
      highlight = {
        enable = true,
      },

      -- Włącz moduł wcięć oparty na treesitter
      indent = {
        enable = true,
      },

      -- Automatyczne instalowanie brakujących parserów
      auto_install = true,
    })
  end,
}
