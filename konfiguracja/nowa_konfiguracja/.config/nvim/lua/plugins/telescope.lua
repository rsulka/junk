-- [[ plugins/telescope.lua ]]

return {
  "nvim-telescope/telescope.nvim",
  branch = "0.1.x",
  dependencies = { "nvim-lua/plenary.nvim" },
  config = function()
    local telescope = require("telescope")
    local actions = require("telescope.actions")

    telescope.setup({
      defaults = {
        path_display = { "truncate" },
        mappings = {
          i = {
            ["<C-k>"] = actions.move_selection_previous, -- poruszaj się w górę
            ["<C-j>"] = actions.move_selection_next, -- poruszaj się w dół
            ["<C-q>"] = actions.send_to_qflist + actions.open_qflist,
          },
        },
      },
    })

    local keymap = vim.keymap
    -- Skróty do wyszukiwania
    keymap.set("n", "<leader>ff", "<cmd>Telescope find_files<cr>", { desc = "Szukaj plików" })
    keymap.set("n", "<leader>fg", "<cmd>Telescope live_grep<cr>", { desc = "Szukaj tekstu w projekcie" })
    keymap.set("n", "<leader>fb", "<cmd>Telescope buffers<cr>", { desc = "Szukaj w otwartych buforach" })
    keymap.set("n", "<leader>fh", "<cmd>Telescope help_tags<cr>", { desc = "Szukaj w tagach pomocy" })
  end,
}
