-- [[ plugins/formatter.lua ]]

return {
  "stevearc/conform.nvim",
  event = { "BufWritePre" },
  cmd = { "ConformInfo" },
  config = function()
    local conform = require("conform")

    conform.setup({
      -- Ustawienie formatowania przy zapisie
      format_on_save = {
        timeout_ms = 500,
        lsp_fallback = true,
      },

      -- Definicje formatterów
      formatters_by_ft = {
        python = { "black" },
        sh = { "shfmt" },
        bash = { "shfmt" },
        lua = { "stylua" },
      },
    })

    -- Dodajemy też stylua do instalacji przez Mason
    -- To sformatuje naszą własną konfigurację :)
    local mason_lspconfig = require("mason-lspconfig")
    mason_lspconfig.setup({
        ensure_installed = { "stylua" }
    })

    -- Skrót klawiszowy do ręcznego formatowania
    vim.keymap.set({ "n", "v" }, "<leader>lf", function()
      conform.format({ async = true, lsp_fallback = true })
    end, { desc = "Formatuj bufor" })
  end,
}
