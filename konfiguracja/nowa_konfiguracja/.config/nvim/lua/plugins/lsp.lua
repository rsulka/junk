-- [[ plugins/lsp.lua ]]

return {
  "neovim/nvim-lspconfig",
  dependencies = {
    "williamboman/mason.nvim",
    "williamboman/mason-lspconfig.nvim",
    "hrsh7th/nvim-cmp",
    "hrsh7th/cmp-nvim-lsp",
    "hrsh7th/cmp-buffer",
    "hrsh7th/cmp-path",
    "L3MON4D3/LuaSnip",
    "saadparwaiz1/cmp_luasnip",
  },
  config = function()
    local cmp = require("cmp")
    local lspconfig = require("lspconfig")
    local keymap = vim.keymap

    -- [[ Konfiguracja autouzupełniania (nvim-cmp) ]]
    cmp.setup({
      snippet = {
        expand = function(args) require("luasnip").lsp_expand(args.body) end,
      },
      mapping = cmp.mapping.preset.insert({
        ['<C-b>'] = cmp.mapping.scroll_docs(-4),
        ['<C-f>'] = cmp.mapping.scroll_docs(4),
        ['<C-Space>'] = cmp.mapping.complete(),
        ['<C-e>'] = cmp.mapping.abort(),
        ['<CR>'] = cmp.mapping.confirm({ select = true }),
      }),
      sources = cmp.config.sources({
        { name = "nvim_lsp" },
        { name = "luasnip" },
      }, {
        { name = "buffer" },
        { name = "path" },
      }),
    })

    -- [[ Funkcja on_attach (co robić, gdy LSP startuje) ]]
    local on_attach = function(client, bufnr)
      local opts = { buffer = bufnr, remap = false }
      keymap.set("n", "gd", vim.lsp.buf.definition, opts)
      keymap.set("n", "K", vim.lsp.buf.hover, opts)
      keymap.set("n", "<leader>vws", vim.lsp.buf.workspace_symbol, opts)
      keymap.set("n", "<leader>vd", vim.diagnostic.open_float, opts)
      keymap.set("n", "[d", vim.diagnostic.goto_next, opts)
      keymap.set("n", "]d", vim.diagnostic.goto_prev, opts)
      keymap.set("n", "<leader>vca", vim.lsp.buf.code_action, opts)
      keymap.set("n", "<leader>vrn", vim.lsp.buf.rename, opts)
    end

    -- [[ Konfiguracja Mason ]]
    require("mason").setup()

    -- [[ Konfiguracja Mason-LSPConfig ]]
    -- Upewniamy się, że wszystkie potrzebne narzędzia są zainstalowane
    require("mason-lspconfig").setup({
      ensure_installed = {
        "lua_ls",
        "pyright",
        "bashls",
        "ts_ls", -- Nowa nazwa dla serwera TypeScript
        "html",
        "cssls",
      }
    })

    -- [[ Konfiguracja serwerów LSP ]]
    -- Lista serwerów do skonfigurowania
    local servers = { "lua_ls", "pyright", "bashls", "ts_ls", "html", "cssls" }

    for _, server_name in ipairs(servers) do
      lspconfig[server_name].setup({
        on_attach = on_attach,
      })
    end
  end,
}