
" Disable compatibility with vi
set nocompatible

" The encoding displayed.
set encoding=utf-8

" The encoding written to file.
set fileencoding=utf-8

" Disable mouse
set mouse-=a

" Configure backspace so it acts as it should act
set backspace=eol,start,indent
set whichwrap+=<,>,h,l

" Enable filetype plugins
filetype plugin on
filetype indent on

" Enable syntax highlighting
syntax enable

" Add numbers to each line on the left-hand side.
set number

" Use spaces instead of tabs
set expandtab

" Be smart when using tabs ;)
set smarttab

" 1 tab == 4 spaces
set shiftwidth=4
set tabstop=4

" Turn backup off, since most stuff is in SVN, git etc. anyway...
set nobackup
set nowb
set noswapfile

" Do not wrap lines.
set nowrap

" Ignore case when searching
set ignorecase

" When searching try to be smart about cases
set smartcase

" Highlight search results
set hlsearch

" While searching though a file incrementally highlight matching characters as you type.
set incsearch

" Show matching brackets when text indicator is over them
set showmatch

" Show the mode you are on the last line.
set noshowmode

" Sets how many lines of history VIM has to remember
set history=1000

" Add a bit extra margin to the left
set foldcolumn=1

" Enable 24-bit RGB color values
set termguicolors

" Turn on the Wild menu
set wildmenu
set wildmode=list:longest
set wildignore=*.docx,*.jpg,*.png,*.gif,*.pdf,*.pyc,*.exe,*.flv,*.img,*.xlsx,*.egp,*.zip,*.gz,*.tar


set background=dark

"colorscheme onedark
colorscheme hybrid

" zo - rozwin
" zc - zamknij
" cR - rozwin wszystko
" zM - zwin wszystko


" PLUGINS ---------------------------------------------------------------- {{{


" }}}


" MAPPINGS --------------------------------------------------------------- {{{


" }}}


" VIMSCRIPT -------------------------------------------------------------- {{{

" This will enable code folding.
" Use the marker method of folding.
augroup filetype_vim
    autocmd!
    autocmd FileType vim setlocal foldmethod=marker
augroup END


" }}}


" STATUS LINE ------------------------------------------------------------ {{{
"



set laststatus=2
set statusline=
set statusline+=%2*
set statusline+=%{StatuslineMode()}
set statusline+=%1*
set statusline+=\ 
set statusline+=%m
set statusline+=%h
set statusline+=%r
set statusline+=%3*
set statusline+=\ %{b:gitbranch}
set statusline+=%1*
set statusline+=%4*
set statusline+=%F
set statusline+=%1*
set statusline+=\ 
set statusline+=\ 
set statusline+=\ [%Y]
set statusline+=\ %{''.(&fenc!=''?&fenc:&enc).''}
set statusline+=\ (%{&ff}) 
set statusline+=%=
set statusline+=%5*
set statusline+=\ COLUMN:\ %-3c
set statusline+=\ LINE:\ %-4l
set statusline+=\ %3p%%
set statusline+=\ %4L
set statusline+=L
"set statusline+=\ %3p%%
set statusline+=%1*
set statusline+=|


hi User2 ctermbg=lightmagenta ctermfg=black guibg=lightmagenta guifg=black
hi User1 ctermbg=black ctermfg=white guibg=black guifg=white
hi User3 ctermbg=black ctermfg=lightblue guibg=black guifg=lightblue
hi User4 ctermbg=black ctermfg=lightgreen guibg=black guifg=lightgreen
hi User5 ctermbg=black ctermfg=magenta guibg=black guifg=magenta

function! StatuslineMode()
    let l:mode=mode()
    if l:mode==#"n"
        return "NORMAL"
    elseif l:mode==?"v"
        return "VISUAL"
    elseif l:mode==#"i"
        return "INSERT"
    elseif l:mode==#"R"
        return "REPLACE"
    elseif l:mode==?"s"
        return "SELECT"
    elseif l:mode==#"t"
        return "TERMINAL"
    elseif l:mode==#"c"
        return "COMMAND"
    elseif l:mode==#"!"
        return "SHELL"
    endif
endfunction

function! StatuslineGitBranch()
    let b:gitbranch=""
    if &modifiable
        try
            let l:dir=expand('%:p:h')
            let l:gitrevparse = system("git -C ".l:dir." rev-parse --abbrev-ref HEAD")
            if !v:shell_error
                let b:gitbranch="GIT:(".substitute(l:gitrevparse, '\n', '', 'g').") "
            endif
        catch
        endtry
    endif
endfunction

augroup GetGitBranch
    autocmd!
    autocmd VimEnter,WinEnter,BufEnter * call StatuslineGitBranch()
augroup END

" }}}
