# Tmux — Cheatsheet (PL)

Spis najczęstszych poleceń `tmux`. Wszystkie polecenia z prefiksem należy poprzedzić wciśnięciem **`Ctrl-a`**.

## Spis treści

- [Sesje (Sessions)](#sesje-sessions)
- [Okna (Windows)](#okna-windows)
- [Panele (Panes)](#panele-panes)
- [Nawigacja](#nawigacja)
- [Kopiowanie (Copy Mode)](#kopiowanie-copy-mode)
- [Mysz i schowek (Mouse/Clipboard)](#mysz-i-schowek-mouseclipboard)
- [Synchronizacja paneli](#synchronizacja-paneli)
- [Bufory (Buffers)](#bufory-buffers)
- [Przenoszenie paneli/okien](#przenoszenie-paneliokien)
- [Drzewo (choose-tree)](#drzewo-choose-tree)
- [Status bar i indeksy](#status-bar-i-indeksy)
- [Wygodne bindy (splity/resize)](#wygodne-bindy-splityresize)
- [Najczęstsze problemy](#najczęstsze-problemy)
- [Inne](#inne)
- [Pluginy](#pluginy)

---

## Sesje (Sessions)

Polecenia używane w terminalu (poza tmux).

| Polecenie | Opis |
| :--- | :--- |
| `tmux new -s <nazwa>` | Tworzy nową sesję o podanej nazwie. |
| `tmux ls` | Wyświetla listę aktywnych sesji. |
| `tmux a -t <nazwa>` | Dołącza do istniejącej sesji. |
| `tmux kill-session -t <nazwa>` | Zabija sesję. |
| `tmux kill-server` | Zabija wszystkie sesje. |

Polecenia z prefiksem **`Ctrl-a`**.

| Skrót | Opis |
| :--- | :--- |
| `d` | Odłącza od bieżącej sesji. |
| `$` | Zmienia nazwę bieżącej sesji. |
| `(` | Przełącza do poprzedniej sesji. |
| `)` | Przełącza do następnej sesji. |

---

## Okna (Windows)

| Skrót | Opis |
| :--- | :--- |
| `c` | Tworzy nowe okno. |
| `,` | Zmienia nazwę bieżącego okna. |
| `w` | Wyświetla listę okien (interaktywna). |
| `&` | Zabija bieżące okno (z potwierdzeniem). |
| `p` | Przełącza do poprzedniego okna. |
| `n` | Przełącza do następnego okna. |
| `0-9` | Przełącza do okna o podanym numerze. |
| `f` | Wyszukuje okno po nazwie. |
| `i` | Wyświetla informacje o bieżącym oknie. |
| `.` | Pozwala przenieść okno na inną pozycję (interaktywnie). |

**Twoje skróty (bez prefiksu):**

| Skrót | Opis |
| :--- | :--- |
| `Ctrl`+`→` | Następne okno. |
| `Ctrl`+`←` | Poprzednie okno. |

---

## Panele (Panes)

**Twoje skróty:**

| Skrót | Opis |
| :--- | :--- |
| `h` | Dzieli panel **pionowo** (nowy po prawej). |
| `v` | Dzieli panel **poziomo** (nowy na dole). |

**Standardowe skróty:**

| Skrót | Opis |
| :--- | :--- |
| `x` | Zabija bieżący panel. |
| `z` | Powiększa/zmniejsza bieżący panel (zoom). |
| `o` | Przełącza do następnego panelu. |
| `;` | Przełącza do ostatnio aktywnego panelu. |
| `{` | Przenosi bieżący panel w lewo. |
| `}` | Przenosi bieżący panel w prawo. |
| `Space` | Zmienia układ paneli. |
| `q` | Pokazuje numery paneli. |
| `!` | "Wybija" bieżący panel do nowego okna. |
| `Ctrl`+`o` | Obraca panelami w oknie. |
| `Alt`+`1..5` | Stosuje predefiniowane układy paneli. |
| `strzałki` | Zmienia rozmiar panelu (trzymając prefiks). |

---

## Nawigacja

**Twoje skróty (z prefiksem `Ctrl-a`):**

| Skrót | Opis |
| :--- | :--- |
| `h` | Wybiera panel po lewej. |
| `j` | Wybiera panel na dole. |
| `k` | Wybiera panel na górze. |
| `l` | Wybiera panel po prawej. |

**Twoje skróty (bez prefiksu):**

| Skrót | Opis |
| :--- | :--- |
| `Shift`+`↑` | Wybiera panel na górze. |
| `Shift`+`↓` | Wybiera panel na dole. |
| `Shift`+`←` | Wybiera panel po lewej. |
| `Shift`+`→` | Wybiera panel po prawej. |

---

## Kopiowanie (Copy Mode)

W trybie kopiowania dostępne są skróty podobne do Vima.

| Skrót | Opis |
| :--- | :--- |
| `[` | Wchodzi w tryb kopiowania (Copy Mode). |
| `]` | Wkleja ostatnio skopiowany tekst. |
| `q` | Opuszcza tryb kopiowania. |
| `g` | Skok na początek historii. |
| `G` | Skok na koniec historii. |
| `h, j, k, l` | Nawigacja w tekście. |
| `v` lub `Space` | Rozpoczyna zaznaczanie. |
| `y` lub `Enter` | Kopiuje zaznaczony tekst do bufora tmux. |
| `/` | Wyszukiwanie w tekście. |
| `n` / `N` | Następny / poprzedni wynik wyszukiwania. |

---

## Mysz i schowek (Mouse/Clipboard)

Polecenia w wierszu poleceń tmux (po naciśnięciu `:`):

| Polecenie | Opis |
| :--- | :--- |
| `set -g mouse on` | Włącza obsługę myszy (przewijanie, wybór paneli, zmiana rozmiaru). |
| `set -g mouse off` | Wyłącza obsługę myszy. |
| `set -g set-clipboard on` | Integruje tmux ze schowkiem systemowym (jeśli wspierane). |

Wskazówki:

- Na Linuksie warto zainstalować `xclip` (X11) lub `wl-clipboard` (Wayland), aby kopiowanie działało do schowka systemowego.
- Przewijanie kółkiem myszy aktywuje Copy Mode; zaznacz tekst i skopiuj klawiszem `Enter`/`y`.

Przykładowa integracja z systemowym schowkiem (w pliku `~/.tmux.conf`):

```bash
# tryb vi w copy-mode i kopiowanie do systemowego schowka
set -g mode-keys vi
bind -T copy-mode-vi y send -X copy-pipe-and-cancel "xclip -selection clipboard -in"
```

### Wayland: wl-clipboard

Jeśli używasz środowiska Wayland (np. GNOME/KDE na Wayland), preferuj `wl-clipboard`:

1. Zainstaluj `wl-clipboard`.
2. Upewnij się, że terminal wspiera OSC52 lub pozostaw poniższe mapowanie, które wymusi kopiowanie przez `wl-copy`.
3. Dodaj do `~/.tmux.conf`:

```tmux
set -g mode-keys vi
set -g set-clipboard on
bind -T copy-mode-vi v send -X begin-selection
bind -T copy-mode-vi y send -X copy-pipe-and-cancel 'wl-copy'
```

Uwagi:

- `wl-copy` umieszcza tekst w schowku graficznym; `wl-paste` odczytuje.
- Niektóre terminale (np. wezterm, kitty) dobrze wspierają OSC52; wtedy `set-clipboard on` może wystarczyć bez dodatkowego binda.

### WezTerm (OSC52 + truecolor)

WezTerm ma bardzo dobre wsparcie OSC52 (kopiowanie przez terminal) i truecolor. Rekomendacje:

1. W tmux włącz OSC52 i tryb vi:

```tmux
set -g mode-keys vi
set -g set-clipboard on
```

1. Opcjonalnie dodaj fallback na `wl-copy`/`xclip` (gdyby OSC52 było wyłączone):

```tmux
bind -T copy-mode-vi y send -X copy-pipe-and-cancel "sh -lc 'if command -v wl-copy >/dev/null 2>&1; then wl-copy; elif command -v xclip >/dev/null 2>&1; then xclip -selection clipboard -in; else cat >/dev/null; fi'"
```

1. Upewnij się, że truecolor jest włączony:

```tmux
set -g default-terminal "xterm-256color"
set -as terminal-overrides ',xterm-256color:RGB'
```

1. Minimalna konfiguracja w `~/.wezterm.lua` (opcjonalnie):

```lua
local wezterm = require 'wezterm'
return {
  enable_wayland = true, -- jeśli używasz Wayland
  color_scheme = 'Catppuccin Mocha',
  keys = {
    -- pozwól tmuxowi przejąć klawisze (zachowaj własne mapowania tmuxa)
  },
}
```

Uwagi:

- WezTerm domyślnie wspiera OSC52; `set -g set-clipboard on` często wystarczy.
- Gdy kopiowanie nie trafia do schowka, sprawdź ustawienia bezpieczeństwa OSC52 w WezTerm oraz włączony Wayland/X11.

---

## Synchronizacja paneli

Wysyła te same klawisze do wszystkich paneli w oknie (bardzo przydatne przy pracy na wielu serwerach jednocześnie).

| Polecenie | Opis |
| :--- | :--- |
| `setw synchronize-panes on` | Włącza synchronizację paneli. |
| `setw synchronize-panes off` | Wyłącza synchronizację paneli. |

---

## Bufory (Buffers)

Tmux przechowuje skopiowane fragmenty w buforach. Możesz je przeglądać, zapisywać i wklejać.

| Polecenie | Opis |
| :--- | :--- |
| `list-buffers` | Lista buforów. |
| `choose-buffer` | Interaktywny wybór bufora do podglądu/wklejenia. |
| `show-buffer -b <id>` | Podgląd zawartości bufora. |
| `save-buffer [-b <id>] <plik>` | Zapisuje bufor do pliku. |
| `delete-buffer -b <id>` | Usuwa bufor. |
| `paste-buffer` | Wkleja ostatni (lub wskazany) bufor. |

---

## Przenoszenie paneli/okien

| Polecenie | Opis |
| :--- | :--- |
| `break-pane` | Wybij bieżący panel do nowego okna (jak `!`). |
| `join-pane -s <okno.pane> -t <okno.pane>` | Przenieś panel między oknami. |
| `swap-pane -s <a> -t <b>` | Zamień panele miejscami (również pomiędzy oknami). |
| `move-window -t <nr>` | Przenieś okno na podany numer. |
| `swap-window -s <a> -t <b>` | Zamień okna numerami. |
| `move-window -r` | Renumeruj okna (uporządkuj numerację). |

---

## Drzewo (choose-tree)

Interaktywny podgląd i nawigacja po sesjach/oknach/panelach.

| Skrót | Opis |
| :--- | :--- |
| `s` | Otwiera „drzewo” (choose-tree) sesji/okien/paneli. |

---

## Status bar i indeksy

Przydatne ustawienia numeracji i paska statusu w `~/.tmux.conf`.

```tmux
# okna/panele numerowane od 1
set -g base-index 1
setw -g pane-base-index 1

# renumeracja okien po usunięciu któregoś
set -g renumber-windows on

# podstawowy pasek statusu
set -g status on
set -g status-interval 5
set -g status-left '#S '
set -g status-right '#H | %H:%M %d-%b'
```

Wskazówki:

- `#S` to nazwa sesji, `#H` to hostname. Datę/czas możesz dopasować formatami `%`.
- Jeśli używasz pluginów, pasek można rozbudować (bateria, git, sieć itd.).

---

## Wygodne bindy (splity/resize)

Popularne mapowania, które często przyspieszają pracę. Dodaj do `~/.tmux.conf`:

```tmux
# szybkie splity: prefix + | oraz prefix + -
bind | split-window -h
bind - split-window -v

# wygodne zmienianie rozmiaru: prefix + H/J/K/L (przytrzymanie powtarza)
bind -r H resize-pane -L 5
bind -r J resize-pane -D 5
bind -r K resize-pane -U 5
bind -r L resize-pane -R 5

# łatwe przekazanie prefiksu do zagnieżdżonego tmuxa: prefix + a
bind a send-prefix
```

Uwaga: Masz już własne bindy do splitów i nawigacji — traktuj powyższe jako opcjonalne uzupełnienie.

---

## Najczęstsze problemy

- Schowek na Wayland vs X11:
  - X11: zainstaluj `xclip` i używaj `... | xclip -selection clipboard -in`.
  - Wayland: zainstaluj `wl-clipboard` i używaj `... | wl-copy`.
  - Przykład dla Copy Mode (Wayland):

```tmux
set -g mode-keys vi
bind -T copy-mode-vi y send -X copy-pipe-and-cancel 'wl-copy'
```

- Kopiowanie przez SSH do lokalnego schowka:
  - W tmux ≥ 3.2 włącz `OSC 52`: `set -g set-clipboard on` (terminal musi to wspierać).
  - Jeśli nie działa, rozważ pluginy/rozszerzenia osc52 w edytorze/terminalu.

- Tmux w tmuxie (zagnieżdżony tmux):
  - Używaj `prefix + a` (patrz bind wyżej), aby wysłać prefiks do sesji wewnętrznej.
  - Alternatywnie uruchamiaj z inną nazwą gniazda: `tmux -L alt new -A -s work`.

---

## Inne

| Skrót | Opis |
| :--- | :--- |
| `r` | Przeładowuje plik konfiguracyjny `~/.tmux.conf`. |
| `t` | Wyświetla zegar w bieżącym panelu. |
| `?` | Wyświetla listę wszystkich skrótów. |
| `d` | Odłącza klienta. |
| `:` | Otwiera wiersz poleceń tmux. |
| `PgUp`/`PgDn` | Przewijanie z włączonym `mouse on`. |

---

## Pluginy

### TPM (Tmux Plugin Manager)

| Skrót | Opis |
| :--- | :--- |
| `I` | Instaluje nowe pluginy (zdefiniowane w `.tmux.conf`). |
| `U` | Aktualizuje istniejące pluginy. |
| `Alt`+`u` | Odinstalowuje nieużywane pluginy. |

### Tmux Resurrect

Plugin do zapisywania i przywracania sesji tmux po restarcie komputera.

| Skrót | Opis |
| :--- | :--- |
| `Ctrl-s` | **Zapisuje** stan wszystkich sesji. |
| `Ctrl-r` | **Przywraca** ostatni zapisany stan. |
