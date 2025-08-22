"""Integracja z Bitbucket Server/Cloud: pobieranie PR, klonowanie,..."""
from __future__ import annotations

from abc import ABC, abstractmethod  # Wzorzec projektowy dla wspólnego interfejsu platform
from typing import Any, Optional  # Typy ogólne do adnotacji
import sys  # Dostęp do exit i stderr

import requests  # HTTP komunikacja z API Bitbucket
import urllib3  # Zarządzanie ostrzeżeniami SSL

from config import Config  # Dostęp do konfiguracji (token, host, itp.)
from logger import info, error  # Logowanie w spójnym formacie

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # Wyłączenie ostrzeżeń o weryfikacji certyfikatu (świadome)

__all__ = [  # Publiczne API modułu
    "BitbucketPlatform",
    "BitbucketServerPlatform",
    "BitbucketCloudPlatform",
    "create_platform",
    "get_pull_requests",
]


class BitbucketPlatform(ABC):  # Abstrakcyjna klasa bazowa zapewniająca jednolite metody
    """Abstrakcja platformy Bitbucket (wspólne API dla Server i Cloud)."""

    def __init__(self, repo: str, token: str, project_or_workspace: str):  # Inicjalizacja wspólnych pól
        self.repo = repo  # Nazwa repozytorium Bitbucket
        self.token = token  # Token API (Bearer)
        self.project_or_workspace = project_or_workspace  # Projekt (Server) albo workspace (Cloud)

    @abstractmethod
    def get_api_prs_url(self) -> str:  # Każda implementacja musi dostarczyć poprawny endpoint
        """Zwraca pełny URL endpointu API listy otwartych PR."""
        pass

    @abstractmethod
    def get_clone_url(self) -> str:  # URL do klonowania (różny format Server/Cloud)
        """Zwraca URL używany do klonowania repozytorium (SSH)."""
        pass

    @abstractmethod
    def get_branch_from_pr(self, pr_data: dict[str, Any]) -> Optional[str]:  # Ekstrakcja nazwy gałęzi źródłowej
        """Ekstrahuje nazwę gałęzi źródłowej z obiektu PR."""
        pass

    @abstractmethod
    def is_pr_approved(self, pr_data: dict[str, Any]) -> bool:  # Sprawdzenie czy PR ma akceptację
        """Zwraca True jeśli PR ma co najmniej jedną akceptację."""
        pass

    @abstractmethod
    def get_approval_count(self, pr_data: dict[str, Any]) -> int:  # Liczba akceptacji PR
        """Zwraca liczbę akceptacji PR (liczba reviewerów z approved=True)."""
        pass


class BitbucketServerPlatform(BitbucketPlatform):  # Implementacja dla Bitbucket Server
    """Implementacja dla Bitbucket Server."""

    def __init__(self, repo: str, token: str, project_or_workspace: str, host: str):  # Dodajemy host specyficzny dla Server
        super().__init__(repo, token, project_or_workspace)
        self.host = host  # Nazwa hosta serwera Bitbucket

    def get_api_prs_url(self) -> str:  # Budowa endpointu REST API PR (Server)
        return (
            f"https://{self.host}/rest/api/1.0/projects/{self.project_or_workspace}/repos/"
            f"{self.repo}/pull-requests?state=OPEN&at=refs/heads/master"
        )

    def get_clone_url(self) -> str:  # SSH URL z portem 7999 (domyślnie dla Bitbucket Server)
        return f"ssh://git@{self.host}:7999/{self.project_or_workspace.lower()}/{self.repo}.git"

    def get_branch_from_pr(self, pr_data: dict[str, Any]) -> Optional[str]:  # Specyficzna struktura JSON dla Server
        return pr_data.get("fromRef", {}).get("displayId")

    def is_pr_approved(self, pr_data: dict[str, Any]) -> bool:  # Sprawdzenie flagi approved u reviewerów
        return any(r.get("approved") for r in pr_data.get("reviewers", []))

    def get_approval_count(self, pr_data: dict[str, Any]) -> int:  # Zliczanie akceptacji
        return sum(1 for r in pr_data.get("reviewers", []) if r.get("approved"))


class BitbucketCloudPlatform(BitbucketPlatform):  # Implementacja dla Bitbucket Cloud
    """Implementacja dla Bitbucket Cloud."""

    def get_api_prs_url(self) -> str:  # Endpoint Cloud (v2.0 API) + pobranie participants
        return (
            "https://api.bitbucket.org/2.0/repositories/"
            f"{self.project_or_workspace}/{self.repo}/pullrequests?state=OPEN&fields=%2Bvalues.participants"
        )

    def get_clone_url(self) -> str:  # Format klonowania Cloud
        return f"git@bitbucket.org:{self.project_or_workspace}/{self.repo}.git"

    def get_branch_from_pr(self, pr_data: dict[str, Any]) -> Optional[str]:  # Struktura JSON Cloud
        return pr_data.get("source", {}).get("branch", {}).get("name")

    def is_pr_approved(self, pr_data: dict[str, Any]) -> bool:  # Akceptacje w polu participants
        return any(p.get("approved") for p in pr_data.get("participants", []))

    def get_approval_count(self, pr_data: dict[str, Any]) -> int:  # Zliczanie approved w participants
        return sum(1 for p in pr_data.get("participants", []) if p.get("approved"))


def create_platform(config: Config, repo: str) -> BitbucketPlatform:  # Fabryka instancji platformy
    """Buduje obiekt platformy wg konfiguracji (Server lub Cloud)."""

    is_server_str = config.get("IS_BITBUCKET_SERVER", "false") or "false"  # Flaga w konfiguracji
    is_server = is_server_str.lower() == "true"  # Konwersja na bool
    token = config.get("BITBUCKET_API_TOKEN") or ""  # Token do autoryzacji
    project_or_workspace = config.get("BITBUCKET_PROJECT_OR_WORKSPACE") or ""  # Nazwa projektu/workspace

    if is_server:
        host = config.get("BITBUCKET_HOST") or ""  # Host wymagany tylko dla Server
        info("Tryb: Bitbucket Server")
        return BitbucketServerPlatform(repo, token, project_or_workspace, host)  # Tworzymy implementację Server

    info("Tryb: Bitbucket Cloud")
    return BitbucketCloudPlatform(repo, token, project_or_workspace)  # Zwrot implementacji Cloud


def get_pull_requests(platform: BitbucketPlatform) -> list:  # Pobieranie listy PR
    """Zwraca listę otwartych PR."""
    all_prs, url = [], platform.get_api_prs_url()  # Inicjalizacja kolekcji i startowego URL
    headers = {"Authorization": f"Bearer {platform.token}"}  # Nagłówek autoryzacyjny
    while url:  # Pętla dopóki API wskazuje kolejny URL
        try:
            response = requests.get(url, headers=headers, verify=False)  # Wyłączenie weryfikacji SSL (świadome)
            response.raise_for_status()  # Rzuci wyjątek przy kodach 4xx/5xx
            data = response.json()  # Dekodowanie JSON
            all_prs.extend(data.get("values", []))  # Dodanie aktualnej strony
            url = data.get("next")  # Następny URL (Cloud) lub None gdy brak
        except requests.exceptions.RequestException as exc:  # Dowolny błąd połączenia/HTTP
            error(f"Nie udało się pobrać danych z Bitbucket: {exc}")  # Log błędu
            sys.exit(1) 
    return all_prs  # Zwracamy pełną listę PR
