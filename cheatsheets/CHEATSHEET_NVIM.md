# Neovim — Cheatsheet (PL)

Krótki i praktyczny spis najczęstszych poleceń Neovim. Prefiksy liczbowe (`3w`, `10dd`) działają z większością ruchów i operacji.

## Spis treści

- [Neovim — Cheatsheet (PL)](#neovim--cheatsheet-pl)
  - [Spis treści](#spis-treści)
  - [Tryby i podstawy](#tryby-i-podstawy)
  - [Ruch po tekście (motions)](#ruch-po-tekście-motions)
  - [Wstawianie i edycja](#wstawianie-i-edycja)
  - [Obiekty tekstowe (text objects)](#obiekty-tekstowe-text-objects)
  - [Wybór wizualny](#wybór-wizualny)
  - [Szukanie i zamiana](#szukanie-i-zamiana)
  - [Rejestry i schowek](#rejestry-i-schowek)
  - [Makra i powtarzanie](#makra-i-powtarzanie)
  - [Okno linii poleceń](#okno-linii-poleceń)
  - [Historia cofania (Undo Tree)](#historia-cofania-undo-tree)
  - [Zaznaczanie miejsc i skoki](#zaznaczanie-miejsc-i-skoki)
  - [Wcięcia, formatowanie i składanie (folds)](#wcięcia-formatowanie-i-składanie-folds)
  - [Pliki, zapisywanie, wyjście](#pliki-zapisywanie-wyjście)
  - [Sesje (Sessions)](#sesje-sessions)
  - [Porównywanie plików (Diff)](#porównywanie-plików-diff)
  - [Bufory, okna (splity) i karty (tabs)](#bufory-okna-splity-i-karty-tabs)
  - [Listy Quickfix i Location](#listy-quickfix-i-location)
  - [Terminal w Neovim](#terminal-w-neovim)
  - [Pisownia (spell)](#pisownia-spell)
  - [Telescope (plugin)](#telescope-plugin)
  - [Treesitter (Tree-sitter)](#treesitter-tree-sitter)
  - [Ustawienia przydatne na start](#ustawienia-przydatne-na-start)
  - [Przykłady łączonych poleceń](#przykłady-łączonych-poleceń)

## Tryby i podstawy

- Tryby: Normalny (`<Esc>`), Wstawiania (`i`, `a`, `I`, `A`, `o`, `O`), Wizualny (`v`, `V`, `Ctrl+v`), Linia poleceń (`:`)
- Wyjście do Normal: `<Esc>` lub `Ctrl+[`
- Powtórz ostatnią zmianę: `.`
- Cofnij / Ponów: `u` / `Ctrl+r`
- Pomoc: `:help temat` (np. `:help motions`, `:help :substitute`)

## Ruch po tekście (motions)

- Znaki i słowa: `h` `j` `k` `l`, `w` `e` `b` (słowa), `W` `E` `B` (SŁOWA oddzielone białymi znakami), `ge` (koniec poprzedniego słowa)
- Linie: `0` (początek), `^` (pierwszy nieb. znak), `$` (koniec)
- Plik: `gg` (początek), `G` (koniec), `:{nr}` lub `{nr}G` skok do linii
- Akapit / blok: `{` `}`
- Ekran: `Ctrl+u` (pół strony w górę), `Ctrl+d` (w dół), `Ctrl+b`/`Ctrl+f` (strona)
- Skok do znaku: `f{c}` / `F{c}` (na znak), `t{c}` / `T{c}` (przed znak), `;` / `,` powtórz
- Nawiasy i dopasowania: `%`
- Przewinięcie kursora: `zz` (środek), `zt` (na górę), `zb` (na dół)

## Wstawianie i edycja

- Wejście w insert: `i` (przed), `a` (po), `I` (początek linii), `A` (koniec), `o`/`O` (nowa linia)
- Usuwanie: `x` (znak), `dw` (słowo), `dd` (linia), `d$`/`D` (do końca linii)
- Zmiana (delete+insert): `cw` (słowo), `cc` (linia), `C` (do końca linii), `ci(` (wewnątrz nawiasów)
- Kopiuj/Wklej: `y{ruch}` (yank), `yy` (linia), `p`/`P` (po/przed)
- Zamiana znaków: `r{c}` (pojedynczy), `R` (tryb nadpisywania)
- Łączenie linii: `J`
- Zmiana wielkości liter: `~` (pojedynczo), `gUw`/`guw` (słowo), `gU{ruch}`/`gu{ruch}`
- Inkrement/dekrement liczby: `Ctrl+a` / `Ctrl+x`

## Obiekty tekstowe (text objects)

- Wewnątrz/razem ze słowem: `iw` / `aw`
- Cytaty: `i"` `a"`, `i'` `a'`, ``i` `` `a` ``
- Nawiasy: `i)` `a)`, `i]` `a]`, `i}` `a}`
- Akapit: `ip` / `ap`
- Przykład: `ci"` (zmień wszystko w cudzysłowie), `da)` (usuń z nawiasem)

## Wybór wizualny

- Tryby: `v` (znaki), `V` (linie), `Ctrl+v` (blok prostokątny)
- Operacje: `y` (kopiuj), `d` (usuń), `~`/`U`/`u` (case), `>`/`<` (wcięcia)
- Wstawianie w wielu liniach: blok `Ctrl+v` → `I` lub `A` → tekst → `<Esc>`

## Szukanie i zamiana

- Szukaj: `/wzorzec` (w dół), `?wzorzec` (w górę), `n`/`N` (nast./popr.)
- Opcje wyszukiwania: dodaj `\c` na końcu wzorca dla ignorowania wielkości liter (`/wzorzec\c`)
- Szybkie pod słowem: `*` (w dół), `#` (w górę)
- Zamiana w linii: `:s/stare/nowe/g`
- Zamiana w całym pliku (`%`): `:%s/stare/nowe/gc` (`c` pyta o potwierdzenie, `i` ignoruje wielkość liter)
- Ranges: `:'<,'>s/…/…/g` (zaznaczenie), `:10,20s/…/…/g` (linia 10–20)
- Użyj `\v` dla „very magic” regex: `:%s/\v(foo|bar)\d+/X/g`

## Rejestry i schowek

- Wybór rejestru: `"{r}` np. `"ayy`, `"ap`
- Lista rejestrów: `:reg`
- Schowek systemowy: `"+y`, `"+p` (lub `set clipboard=unnamedplus`)
- Czarna dziura (bez zapisu): `"_d`

## Makra i powtarzanie

- Nagrywanie: `q{r}` rozpocznij, `q` zakończ (np. `qa`)
- Odtwarzanie: `@{r}`, ostatnie: `@@`
- Liczba powtórzeń: `10@a`

## Okno linii poleceń

- Otwórz historię poleceń: `q:`
- Otwórz historię wyszukiwania (w dół): `q/`
- Otwórz historię wyszukiwania (w górę): `q?`
- W oknie historii można edytować i uruchamiać polecenia jak w normalnym buforze.

## Historia cofania (Undo Tree)

- Cofnij / Ponów: `u` / `Ctrl+r`
- Zobacz drzewo zmian: `:undolist`
- Cofnij do konkretnego stanu: `:undo {nr}` z listy `:undolist`
- Podróż w czasie: `:earlier {czas}` (np. `:earlier 10m`), `:later {czas}`

## Zaznaczanie miejsc i skoki

- Znaczniki: `m{a-z}` (lokalne), `m{A-Z}` (globalne/plikowe)
- Skok do znacznika: `'{m}` (początek linii), `` `{m} `` (dokładna pozycja)
- Historia skoków (jumplist): `Ctrl+o` (wstecz), `Ctrl+i` (naprzód)
- Historia zmian (changelist): `g;` (wstecz), `g,` (naprzód)
- Skok do ostatniej zmiany: `'.`
- Powrót do ostatniej pozycji kursora: `` `` ``

## Wcięcia, formatowanie i składanie (folds)

- Wcięcia: `>>` / `<<` (linia), `=` + ruch (auto-indent), `==` (linia)
- Formatowanie tekstu (zawijanie wg `textwidth`): `gq{ruch}`, np. `gqap`
- Składanie: `zc` (zamknij), `zo` (otwórz), `za` (toggle), `zM`/`zR` (wszystko)

## Pliki, zapisywanie, wyjście

- Otwórz: `:e ścieżka`, nowy pusty: `:enew`
- Zapis: `:w`, wszystkie: `:wa`
- Wyjście: `:q`, bez zapisu: `:q!`
- Zapis i wyjście: `:wq`, `:x`, `ZZ`; porzuć bez zapisu: `ZQ`
- Otwórz ścieżkę pod kursorem: `gf`
- Przeglądarka plików (netrw): `:Ex`, `:Sex`, `:Vex` (warto rozważyć zamianę na plugin np. `nvim-tree.lua`)

## Sesje (Sessions)

- Zapisz sesję: `:mksession! ścieżka/do/pliku.vim` (nadpisuje istniejący)
- Wczytaj sesję: `:source ścieżka/do/pliku.vim` lub `nvim -S ścieżka/do/pliku.vim`

## Porównywanie plików (Diff)

- Włącz tryb diff dla okna: `:diffthis`
- Otwórz plik w nowym splicie i porównaj: `:diffsplit ścieżka/do/pliku`
- Nawigacja: `]c` (następna zmiana), `[c` (poprzednia zmiana)
- Pobierz/wyślij zmiany: `:diffget` / `:diffput` (można użyć `do` i `dp` w skrócie)

## Bufory, okna (splity) i karty (tabs)

- Bufory: `:ls` (lista), `:b {nr|frag}` (przełącz), `:bn`/`:bp` (nast./poprz.), `:bd` (zamknij)
- Splity: `:sp` (poziomy), `:vsp` (pionowy), `Ctrl+w s` / `Ctrl+w v`
- Nawigacja po splitach: `Ctrl+w h/j/k/l`, wyrównanie: `Ctrl+w =`, jedyny: `:only`
- Rozmiar: `:resize ±N`, `:vertical resize ±N`
- Karty: `:tabnew`, `gt`/`gT` (nast./popr.), `:tabclose`, `:tabmove {N}`

## Listy Quickfix i Location

- Grep (wyniki w quickfix list): `:grep wzorzec **/*.ext` (używa `grepprg`, np. ripgrep)
- Wewnętrzny grep: `:vimgrep /wzorzec/g **/*.ext`
- Lista Quickfix (globalna): `:copen`, `:cclose`, `:cnext`, `:cprev`, `:cfirst`, `:clast`
- Lista Location (dla okna): `:lopen`, `:lclose`, `:lnext`, `:lprev`
- Wstaw diagnostykę LSP do listy: `:lua vim.diagnostic.setqflist()` lub `setloclist()`


## Terminal w Neovim

- Uruchom: `:terminal`, `:vsp | terminal`, `:sp | terminal`
- Przełącz do Normal z terminala: `Ctrl+\` potem `Ctrl+n`
- Wejście z powrotem do insert w terminalu: `i` lub `a`
- Wskazówka: Można zmapować wyjście z trybu terminala na `<Esc>`, np. `tnoremap <Esc> <C-\\><C-n>`

## Pisownia (spell)

- Włącz/wyłącz: `:set spell` / `:set nospell` (język: `:set spelllang=pl,en`)
- Następny/Poprzedni błąd: `]s` / `[s`
- Propozycje: `z=`
- Dodaj/usuń ze słownika: `zg` / `zw`

## Telescope (plugin)

- Uruchamianie pickerów:
  - `:Telescope find_files` — znajdź pliki (szanuje `.gitignore`)
  - `:Telescope live_grep` — pełnotekstowe wyszukiwanie (wymaga ripgrep)
  - `:Telescope buffers` — otwarte bufory
  - `:Telescope help_tags` — pomoc
  - `:Telescope oldfiles` — ostatnio otwierane
  - `:Telescope grep_string` — szukaj słowa spod kursora
  - Git: `:Telescope git_files`, `:Telescope git_status`, `:Telescope git_branches`
  - LSP: `:Telescope lsp_references`, `lsp_definitions`, `lsp_implementations`, `lsp_type_definitions`, `diagnostics`
- Nawigacja w oknie Telescope (domyślnie):
  - Wejście: `<CR>` (otwórz), `Ctrl-x` (split), `Ctrl-v` (vsplit), `Ctrl-t` (tab)
  - Ruch: `Ctrl-n` / `Ctrl-p` (nast./popr. wynik)
  - Podgląd: `Ctrl-u` / `Ctrl-d` (przewijanie)
  - Quickfix: `Ctrl-q` (wyślij zaznaczone do quickfix + otwórz)
  - Pomoc: `?` (pokaż dostępne skróty)

## Treesitter (Tree-sitter)

- Zarządzanie parserami:
  - `:TSInstall <język>` — instaluj parser
  - `:TSUpdate [<język>]` — aktualizuj (wszystkie lub wybrane)
  - `:TSUninstall <język>` — odinstaluj
- Diagnostyka i inspekcja:
  - `:Inspect` — pokaż źródło highlightu pod kursorem (TS/syntax)
  - `:InspectTree` — drzewo parse (interaktywne)
  - `:TSModuleInfo` — status modułów TS w bieżącym buforze
- Włączanie/wyłączanie w buforze:
  - `:TSBufToggle highlight` / `indent`
- Składanie kodu oparte na TS:
  - `:set foldmethod=expr`
  - `:set foldexpr=nvim_treesitter#foldexpr()`

## Ustawienia przydatne na start

- Podświetlanie wyszukiwania: `:set hlsearch` (wyczyść: `:nohlsearch`)
- Inkrementalne wyszukiwanie: `:set incsearch`
- Numery linii: `:set number` (relatywne: `:set relativenumber`)
- Schowek systemowy: `:set clipboard=unnamedplus`
- Zawijanie linii: `:set wrap` / `:set nowrap`
- Przewijanie kontekstowe: `:set scrolloff=8` (zawsze trzyma 8 linii kontekstu powyżej/poniżej kursora)

## Przykłady łączonych poleceń

- `daw` — usuń całe słowo wraz ze spacją
- `ci"` — zmień tekst wewnątrz cudzysłowu
- `yip` → `p` — skopiuj i wklej akapit
- `:10,20s/foo/bar/gc` — zamień w liniach 10–20 z potwierdzeniem
- `qa` → makro → `q`, następnie `100@a` — powtórz makro 100×

---

Podpowiedź: w razie wątpliwości użyj `:help` z nazwą komendy lub ruchu, np. `:help text-objects`, `:help visual-block`, `:help registers`.