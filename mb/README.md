# Merge Bitbucket (mb)

Skrypt do pobierania i łączenia zmian z otwartych pull requestów w repozytorium Bitbucket.

## Opis

Narzędzie `mb.sh` automatyzuje proces pobierania zmian ze wszystkich (lub tylko zatwierdzonych) otwartych pull requestów dla danego repozytorium. Skrypt analizuje, które pliki zostały zmienione w poszczególnych gałęziach, a następnie tworzy nowy katalog zawierający połączone wersje tych plików.

W przypadku, gdy ten sam plik został zmodyfikowany w wielu pull requestach, skrypt prosi użytkownika o interaktywne rozwiązanie konfliktu poprzez wybór gałęzi, z której ma zostać pobrana ostateczna wersja pliku.

## Wymagania

Przed uruchomieniem skryptu upewnij się, że masz zainstalowane następujące narzędzia:
*   `jq` - do przetwarzania danych JSON z API Bitbucket.
*   `git` - do operacji na repozytorium.

## Konfiguracja

Konfiguracja odbywa się w pliku `.mb_config`, który musi znajdować się w tym samym katalogu co skrypt. Możesz skopiować i zmodyfikować plik `mb_config_sample`.

**Zmienne konfiguracyjne:**

*   `BITBUCKET_HOST`: Adres Twojego serwera Bitbucket (np. `bitbucket.twojafirma.com`) lub `api.bitbucket.org` dla Bitbucket Cloud.
*   `IS_BITBUCKET_SERVER`: Ustaw na `true` jeśli korzystasz z Bitbucket Server lub Data Center. W przeciwnym razie ustaw na `false`.
*   `BITBUCKET_PROJECT_OR_WORKSPACE`:
    *   Dla **Bitbucket Cloud**: nazwa Twojego workspace.
    *   Dla **Bitbucket Server/DC**: klucz projektu.
*   `BITBUCKET_API_TOKEN`: Osobisty token dostępowy z uprawnieniami do odczytu repozytoriów i pull requestów.

## Użycie

Skrypt uruchamia się z poziomu terminala, podając wymagane i opcjonalne parametry.

```bash
./mb.sh -r <nazwa-repozytorium> [-a] [-d /sciezka/do/katalogu]
```

**Parametry:**

*   `-r <nazwa-repozytorium>`: **(Wymagany)** Nazwa repozytorium w Bitbucket.
*   `-a`: **(Opcjonalny)** Jeśli użyty, skrypt pobierze zmiany tylko z tych pull requestów, które zostały zatwierdzone (mają status "approved").
*   `-d <katalog>`: **(Opcjonalny)** Ścieżka do katalogu, w którym zostaną umieszczone połączone pliki. Domyślnie jest to `~/<nazwa-repozytorium>_merged`.

### Przykład

Aby połączyć wszystkie zmiany z otwartych PR w repozytorium o nazwie `moj-projekt`, użyj polecenia:
```bash
./mb.sh -r moj-projekt
```

Aby połączyć tylko zatwierdzone zmiany i zapisać je w katalogu `/tmp/moj-projekt-polaczony`:
```bash
./mb.sh -r moj-projekt -a -d /tmp/moj-projekt-polaczony
```
