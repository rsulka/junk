" =============================================================================
"  GŁÓWNA KONFIGURACJA VIM
" =============================================================================

" Wyłącz kompatybilność z Vi na samym początku, aby umożliwić nowoczesne funkcje Vima.
set nocompatible

" =============================================================================
"  MENEDŻER WTYCZEK: VIM-PLUG
" =============================================================================
" Rozpocznij sekcję definiowania wtyczek. Będą one instalowane w folderze ~/.vim/plugged.
call plug#begin('~/.vim/plugged')

" Wygląd
Plug 'ghifarit53/tokyonight-vim'  " Motyw kolorystyczny Tokyonight
Plug 'itchyny/lightline.vim'     " Lekki i konfigurowalny pasek statusu (alternatywa dla airline)
Plug 'ryanoasis/vim-devicons'    " Ikony dla typów plików (używane przez inne wtyczki)

" Funkcjonalność
Plug 'junegunn/fzf', { 'do': { -> fzf#install() } } " Rozmyta wyszukiwarka plików (backend)
Plug 'junegunn/fzf.vim'                             " Integracja fzf z Vimem
Plug 'airblade/vim-gitgutter'                       " Pokazuje zmiany Git w kolumnie przy numerach linii
Plug 'jiangmiao/auto-pairs'                        " Automatycznie zamyka nawiasy, cudzysłowy itp.

" Linter
Plug 'dense-analysis/ale'        " Asynchroniczny silnik do lintowania (sprawdzania błędów) i formatowania

" Formatter
Plug 'sbdchd/neoformat'          " Uniwersalna wtyczka do formatowania kodu

" Zakończ sekcję definiowania wtyczek.
call plug#end()


" =============================================================================
"  PODSTAWOWE OPCJE
" =============================================================================

" Poprawka na kody sterujące (escape codes) w niektórych terminalach, zapobiega "krzaczkom".
if &term =~ 'xterm'
  let &t_RB = ''
  let &t_RF = ''
endif

" Włącz obsługę wtyczek i wcięć specyficznych dla typu pliku.
filetype plugin on
filetype indent on

" Włącz podświetlanie składni.
syntax enable

" Ustaw kodowanie znaków na UTF-8 dla interfejsu i plików.
set encoding=utf-8
set fileencoding=utf-8

" Pokaż numerację linii.
set number
" Pokaż relatywne numery linii (przydatne do skakania o X linii w górę/dół).
set relativenumber

" Włącz obsługę 24-bitowych kolorów ("true color") dla lepszego wyglądu motywów.
set termguicolors

" Zawsze pokazuj kolumnę po lewej na znaki (błędy, zmiany Git).
set signcolumn=yes

" Podświetlaj pasujące nawiasy.
set showmatch

" Wyłącz domyślny wskaźnik trybu Vima (np. -- INSERT --), bo pasek statusu go zastępuje.
set noshowmode
" Zawsze pokazuj pasek statusu (2 = zawsze, 1 = gdy są co najmniej 2 okna, 0 = nigdy).
set laststatus=2

" Dodaj mały margines (1 kolumnę) po lewej stronie na znaczniki zwijania kodu.
set foldcolumn=1

" Ustawienia wcięć: używaj spacji zamiast tabulatorów.
set expandtab
" Włącz "inteligentny" tabulator, który dostosowuje się do wcięć.
set smarttab
" Ustaw szerokość tabulatora i wcięcia na 4 spacje.
set tabstop=4
set shiftwidth=4

" Automatycznie ustawiaj wcięcie w nowej linii na takie samo jak w poprzedniej.
set autoindent

" Wyłącz zawijanie długich linii.
set nowrap

" Trzymaj zawsze 8 linii kontekstu powyżej i poniżej kursora podczas przewijania.
set scrolloff=8
set sidescrolloff=8

" Ustaw liczbę zapamiętywanych poleceń w historii na 1000.
set history=1000

" Pozwól klawiszowi Backspace na usuwanie wcięć, końca linii i znaków na początku wstawiania.
set backspace=eol,start,indent
" Pozwól klawiszom strzałek lewo/prawo na przechodzenie do poprzedniej/następnej linii.
set whichwrap+=<,>,h,l

" Wyłącz tworzenie plików zapasowych (*~) i plików wymiany (*.swp).
set nobackup
set nowb
set noswapfile
" Włącz "wieczne" cofanie (historia zmian jest zachowywana po zamknięciu pliku).
set undofile
" Utwórz folder na pliki "undo", jeśli nie istnieje.
if !isdirectory($HOME.'/.vim/undodir')
    call mkdir($HOME.'/.vim/undodir', 'p')
endif
set undodir=~/.vim/undodir

" Ignoruj wielkość liter podczas wyszukiwania...
set ignorecase
" ...chyba że w wyszukiwanej frazie znajduje się wielka litera.
set smartcase

" Podświetlaj wszystkie wyniki wyszukiwania.
set hlsearch
" Pokazuj wyniki wyszukiwania na bieżąco, w trakcie pisania.
set incsearch

" Włącz ulepszone menu uzupełniania dla poleceń w trybie wiersza poleceń.
set wildmenu
set wildmode=list:longest
" Ignoruj określone typy plików podczas uzupełniania nazw plików.
set wildignore=*.docx,*.jpg,*.png,*.gif,*.pdf,*.pyc,*.exe,*.flv,*.img,*.xlsx,*.egp,*.zip,*.gz,*.tar

" Wyłącz obsługę myszy we wszystkich trybach.
set mouse-=a


" =============================================================================
"  MAPOWANIE KLAWISZY
" =============================================================================
" Ustaw klawisz <Leader> na spację. Musi być zdefiniowane PRZED pierwszym użyciem.
let mapleader = ' '
let maplocalleader = ' '

" Tryb Normal
" Lepsze poruszanie się po oknach (splitach)
nnoremap <C-h> <C-w>h " Przełącz okno w lewo
nnoremap <C-l> <C-w>l " Przełącz okno w prawo
nnoremap <C-j> <C-w>j " Przełącz okno w dół
nnoremap <C-k> <C-w>k " Przełącz okno w górę

" Zmiana rozmiaru okien
nnoremap <C-Up> :resize -2<CR> " Zmniejsz okno w pionie
nnoremap <C-Down> :resize +2<CR> " Zwiększ okno w pionie
nnoremap <C-Left> :vertical resize -2<CR> " Zmniejsz okno w poziomie
nnoremap <C-Right> :vertical resize +2<CR> " Zwiększ okno w poziomie

" Wyłączanie podświetlenia ostatniego wyszukiwania
nnoremap <leader>nh :nohl<CR> " Wyłącz podświetlenie wyszukiwania

" Kopiowanie do schowka systemowego
nnoremap <leader>y "+y " Kopiuj do schowka systemowego
vnoremap <leader>y "+y " Kopiuj zaznaczenie do schowka systemowego
nnoremap <leader>Y "+Y " Kopiuj całą linię do schowka systemowego

" Tryb Insert
" Szybkie wyjście do trybu Normal za pomocą 'jk'
inoremap jk <ESC>

" Tryb Visual
" Przesuwanie zaznaczonych linii w górę i w dół
vnoremap J :m '>+1<CR>gv=gv " Przesuń linię w dół
vnoremap K :m '<-2<CR>gv=gv " Przesuń linię w górę


" =============================================================================
"  KONFIGURACJA WTYCZEK
" =============================================================================

" --- Motyw: Tokyonight ---
" Załaduj schemat kolorystyczny Tokyonight.
colorscheme tokyonight

" --- Pasek statusu: lightline ---
" Konfiguracja paska statusu. Poniżej zdefiniowano:
"   - 'colorscheme': Motyw paska pasujący do reszty Vima.
"   - 'active': Komponenty widoczne w aktywnym oknie.
"     - 'left': Tryb Vima, nazwa pliku, status modyfikacji, diagnostyka z lintera.
"     - 'right': Informacje o pozycji w pliku, typ pliku.
"   - 'component_function': Integracja z wtyczką ALE.
"   - 'separator', 'subseparator': Znaki w stylu Powerline dla estetycznego wyglądu.
let g:lightline = {
      \ 'colorscheme': 'tokyonight',
      \ 'active': {
      \   'left': [ [ 'mode', 'paste' ],
      \             [ 'readonly', 'filename', 'modified' ],
      \             [ 'diagnostics' ] ],
      \   'right': [ [ 'lineinfo' ],
      \              [ 'percent' ],
      \              [ 'filetype' ] ]
      \ },
      \ 'component_function': {
      \   'diagnostics': 'ALEGetStatusLine'
      \ },
      \ 'separator': { 'left': '', 'right': '' },
      \ 'subseparator': { 'left': '', 'right': '' }
      \ }

" --- Wyszukiwarka: fzf.vim ---
" Skróty klawiszowe do wywoływania wyszukiwarki fzf.
nnoremap <leader>ff :Files<CR>     " Szukaj plików w bieżącym katalogu
nnoremap <leader>fg :Rg<CR>        " Szukaj tekstu w projekcie (wymaga ripgrep)
nnoremap <leader>fb :Buffers<CR>   " Szukaj w otwartych buforach (plikach)
nnoremap <leader>fh :Helptags<CR>  " Szukaj w dokumentacji pomocy Vima

" --- Formatter: neoformat ---
" Automatycznie formatuj plik przed każdym zapisem.
autocmd BufWritePre * Neoformat
" Definicje formatterów, których ma używać neoformat.
let g:neoformat_python_black = {'exe': 'black'}
let g:neoformat_lua_stylua = {'exe': 'stylua'}
let g:neoformat_sh_shfmt = {'exe': 'shfmt'}
" Jawne włączenie formatterów dla konkretnych typów plików.
let g:neoformat_enabled_python = ['black']
let g:neoformat_enabled_lua = ['stylua']
let g:neoformat_enabled_sh = ['shfmt']
" Skrót do ręcznego formatowania.
nnoremap <leader>lf :Neoformat<CR> " Formatuj bufor

" --- Linter: ALE ---
" Definiuje, który linter ma być używany dla danego typu pliku.
let g:ale_linters = {
\   'python': ['ruff'],
\}
" Definiuje proste auto-poprawki, jak usuwanie spacji na końcu linii.
let g:ale_fixers = {
\   '*': ['remove_trailing_lines', 'trim_whitespace'],
\}
" Uruchamiaj lintowanie przy zapisie pliku i wejściu do bufora.
let g:ale_lint_on_save = 1
let g:ale_lint_on_enter = 1
" Nie uruchamiaj lintowania w trakcie pisania, dla lepszej wydajności.
let g:ale_lint_on_text_changed = 'never'
" Skróty do nawigacji pomiędzy błędami znalezionymi przez ALE.
nmap [d <Plug>(ale_previous_wrap) " Przejdź do poprzedniego błędu
nmap ]d <Plug>(ale_next_wrap) " Przejdź do następnego błędu