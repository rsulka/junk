-- [[ plugins/linter.lua ]]

return {
  "mfussenegger/nvim-lint",
  event = { "BufWritePost", "BufEnter" },
  config = function()
    local lint = require("lint")

    lint.linters_by_ft = {
      python = { "ruff" },
    }

    -- Uruchom linter przy zapisie i wejściu do bufora
    vim.api.nvim_create_autocmd({ "BufWritePost", "BufEnter" }, {
      callback = function()
        lint.try_lint()
      end,
    })
  end,
}
