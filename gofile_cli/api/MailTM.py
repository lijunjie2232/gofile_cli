"""
MailTM API Client Module

This module provides a Python client for the MailTM temporary email service.
It enables account creation, message retrieval, and email management through
a simple and intuitive interface.

Main Classes:
    MailTM: Primary class for interacting with MailTM API endpoints.

Example Usage:
    >>> from gofile_cli.api import MailTM
    >>> mailtm = MailTM()
    >>> account, address, password = mailtm.create_account()
    >>> print(f"Created account: {address}")
"""

import json
import logging
from typing import Optional, Tuple

from requests import Session

from gofile_cli.entity import (Account, Domain, Domains, MailTMInvalidResponse,
                               Messages, MessageSource, OneMessage, Token)
from gofile_cli.utils import random_string, validate_response

logger = logging.getLogger("mailtm")


class MailTM:
    """
    A comprehensive client for the MailTM temporary email service API.
    
    This class provides methods for:
    - Creating temporary email accounts
    - Retrieving and reading messages
    - Managing account settings
    - Deleting accounts and messages
    
    Attributes:
        API_URL (str): Base URL for MailTM API.
        SSL (bool): Whether to verify SSL certificates. Default: False.
        session (Session): Requests session for HTTP operations.
    
    Example:
        >>> mailtm = MailTM()
        >>> account = mailtm.create_account()
        >>> messages = mailtm.get_messages(account)
    """
    API_URL = "https://api.mail.tm"
    SSL = False

    def __init__(
        self,
        session: Optional[Session] = None,
    ):
        """
        Initialize a MailTM client instance.
        
        Args:
            session: Optional Requests session. If not provided, a new session is created.
        """
        self.session = session or Session()

    def get_account_token(
        self,
        address: str,
        password: str,
    ) -> Token:
        """
        Get an authentication token for an existing account.
        
        Args:
            address: Email address of the account.
            password: Password for the account.
        
        Returns:
            Token: Authentication token object.
        
        Raises:
            MailTMInvalidResponse: If the API request fails.
        
        Reference:
            https://docs.mail.tm/#authentication
        """
        headers = {
            "accept": "application/ld+json",
            "Content-Type": "application/json",
        }
        response = self.session.post(
            f"{self.API_URL}/token",
            data=json.dumps({"address": address, "password": password}),
            headers=headers,
            verify=self.SSL,
        )
        logger.debug(f"Response for {self.API_URL}/token: {response}")
        if validate_response(response):
            return Token(**(response.json()))
        logger.debug(f"Error response for {self.API_URL}/token: {response}")
        raise MailTMInvalidResponse(
            f"Error response for {self.API_URL}/token", response.json()
        )

    def get_domains(
        self,
    ) -> Domains:
        """
        Get available email domains.
        
        Returns:
            Domains: Object containing list of available domains.
        
        Raises:
            MailTMInvalidResponse: If the API request fails.
        
        Reference:
            https://docs.mail.tm/#get-domains
        """
        response = self.session.get(
            f"{self.API_URL}/domains",
            verify=self.SSL,
        )
        logger.debug(f"Response for {self.API_URL}/domains: {response}")
        if validate_response(response):
            return Domains(**(response.json()))
        logger.debug(f"Error response for {self.API_URL}/domains: {response}")
        raise MailTMInvalidResponse(
            f"Error response for {self.API_URL}/domains", response.json()
        )

    def get_domain(
        self,
        domain_id: str,
    ) -> Domain:
        """
        Get information about a specific domain.
        
        Args:
            domain_id: ID of the domain to retrieve.
        
        Returns:
            Domain: Domain object containing domain information.
        
        Raises:
            MailTMInvalidResponse: If the API request fails.
        
        Reference:
            https://docs.mail.tm/#get-domainsid
        """
        response = self.session.get(
            f"{self.API_URL}/domains/{domain_id}", verify=self.SSL
        )
        logger.debug(f"Response for {self.API_URL}/domains/{domain_id}: {response}")
        if validate_response(response):
            return Domain(**(response.json()))
        logger.debug(
            f"Error response for {self.API_URL}/domains/{domain_id}: {response}"
        )
        raise MailTMInvalidResponse(
            f"Error response for {self.API_URL}/domains/{domain_id}",
            response.json(),
        )

    def create_account(
        self,
    ) -> Tuple[Account, str, str]:
        """
        Create a new temporary email account with random credentials.
        
        Returns:
            Tuple[Account, str, str]: A tuple containing (account, address, password).
        
        Example:
            >>> account, address, password = mailtm.create_account()
            >>> print(f"Email: {address}, Password: {password}")
        """
        domain = (self.get_domains()).hydra_member[0].domain
        address = f"{random_string()}@{domain}"
        password = random_string()
        account = self.get_account(
            address=address,
            password=password,
        )
        return account, address, password

    def get_account(
        self,
        address: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Account:
        """
        Create a new account with specified or random credentials.
        
        Args:
            address: Optional email address. If None, a random address is generated.
            password: Optional password. If None, a random password is generated.
        
        Returns:
            Account: Account object with authentication token.
        
        Raises:
            MailTMInvalidResponse: If the API request fails.
        
        Reference:
            https://docs.mail.tm/#post-accounts
        """
        if address is None:
            domain = (self.get_domains()).hydra_member[0].domain
            address = f"{random_string()}@{domain}"
        if password is None:
            password = random_string()
        payload = {"address": address, "password": password}
        logger.debug(f"Create account with payload: {payload}")
        response = self.session.post(
            f"{self.API_URL}/accounts", json=payload, verify=self.SSL
        )
        logger.debug(f"Response for {self.API_URL}/accounts: {response}")
        if validate_response(response):
            response = response.json()
            token = self.get_account_token(
                address=address,
                password=password,
            )
            response["token"] = token
            return Account(**response)
        logger.debug(f"Error response for {self.API_URL}/accounts: {response}")
        raise MailTMInvalidResponse(
            f"Error response for {self.API_URL}/accounts",
            response.json(),
        )

    def get_account_by_id(
        self,
        account_id: str,
        token: str,
    ) -> Account:
        """
        Get account information by account ID.
        
        Args:
            account_id: ID of the account to retrieve.
            token: Authentication token.
        
        Returns:
            Account: Account object with full details.
        
        Raises:
            MailTMInvalidResponse: If the API request fails.
        
        Reference:
            https://docs.mail.tm/#get-accountsid
        """
        response = self.session.get(
            f"{self.API_URL}/accounts/{account_id}",
            headers={"Authorization": f"Bearer {token}"},
            verify=self.SSL,
        )
        logger.debug(f"Response for {self.API_URL}/accounts/{account_id}: {response}")
        if validate_response(response):
            data = response.json()
            if "token" not in data:
                data["token"] = Token(**({"id": account_id, "token": token}))
            return Account(**data)
        logger.debug(
            f"Error response for {self.API_URL}/accounts/{account_id}: {response}"
        )
        raise MailTMInvalidResponse(
            f"Error response for {self.API_URL}/accounts/{account_id}",
            response.json(),
        )

    def delete_account_by_id(
        self,
        mail: Optional[Account] = None,
        account_id: str = "",
        token: str = "",
    ) -> bool:
        """
        Delete an account by ID.
        
        Args:
            mail: Account object. Either this or (account_id and token) must be provided.
            account_id: ID of the account to delete.
            token: Authentication token.
        
        Returns:
            bool: True if deletion was successful.
        
        Raises:
            AssertionError: If required parameters are not provided.
            MailTMInvalidResponse: If the API request fails.
        
        Reference:
            https://docs.mail.tm/#delete-accountsid
        """
        assert mail or (account_id and token), "account_id and token must be provided"
        account_id = account_id or mail.id
        token = token or mail.token.token
        if isinstance(token, Token):
            token = token.token
        response = self.session.delete(
            f"{self.API_URL}/accounts/{account_id}",
            headers={"Authorization": f"Bearer {token}"},
            verify=self.SSL,
        )
        logger.debug(f"Response for {self.API_URL}/accounts/{account_id}: {response}")
        if validate_response(response):
            return response.status == 204
        logger.debug(
            f"Error response for {self.API_URL}/accounts/{account_id}: {response}"
        )
        raise MailTMInvalidResponse(
            f"Error response for {self.API_URL}/accounts/{account_id}",
            response.json(),
        )

    def get_me(
        self,
        token: Union[str, Token],
    ) -> Account:
        """
        Get current authenticated user's account information.
        
        Args:
            token: Authentication token (string or Token object).
        
        Returns:
            Account: Current user's account object.
        
        Raises:
            MailTMInvalidResponse: If the API request fails.
        
        Reference:
            https://docs.mail.tm/#get-me
        """
        if isinstance(token, Token):
            token = token.token
        response = self.session.get(
            f"{self.API_URL}/me",
            headers={"Authorization": f"Bearer {token}"},
            verify=self.SSL,
        )
        logger.debug(f"Response for {self.API_URL}/me: {response}")
        if validate_response(response):
            data = response.json()
            if "token" not in data:
                data["token"] = Token(**({"id": data["id"], "token": token}))
            return Account(**data)
        logger.debug(f"Error response for {self.API_URL}/me: {response}")
        raise MailTMInvalidResponse(
            f"Error response for {self.API_URL}/me", response.json()
        )

    def get_messages(
        self,
        account: Optional[Account] = None,
        token: str = "",
        page: int = 1,
    ) -> Messages:
        """
        Get messages for an account.
        
        Args:
            account: Account object. Either this or 'token' must be provided.
            token: Authentication token.
            page: Page number for pagination. Default: 1.
        
        Returns:
            Messages: Object containing list of messages.
        
        Raises:
            AssertionError: If neither account nor token is provided.
            MailTMInvalidResponse: If the API request fails.
        
        Reference:
            https://docs.mail.tm/#get-messages
        """
        token = token or account.token.token
        response = self.session.get(
            f"{self.API_URL}/messages?page={page}",
            headers={"Authorization": f"Bearer {token}"},
            verify=self.SSL,
        )
        logger.debug(f"Response for {self.API_URL}/messages: {response}")
        if validate_response(response):
            return Messages(**(response.json()))
        logger.debug(f"Error response for {self.API_URL}/messages: {response}")
        raise MailTMInvalidResponse(
            f"Error response for {self.API_URL}/messages", response.json()
        )

    def get_message_by_id(
        self,
        message_id: str,
        account: Optional[Account] = None,
        token: str = "",
    ) -> OneMessage:
        """
        Get a specific message by ID.
        
        Args:
            message_id: ID of the message to retrieve.
            account: Account object. Either this or 'token' must be provided.
            token: Authentication token.
        
        Returns:
            OneMessage: Complete message object with content.
        
        Raises:
            AssertionError: If neither account nor token is provided.
            MailTMInvalidResponse: If the API request fails.
        
        Reference:
            https://docs.mail.tm/#get-messagesid
        """
        token = token or account.token.token
        response = self.session.get(
            f"{self.API_URL}/messages/{message_id}",
            headers={"Authorization": f"Bearer {token}"},
            verify=self.SSL,
        )
        logger.debug(f"Response for {self.API_URL}/messages/{message_id}: {response}")
        if validate_response(response):
            return OneMessage(**(response.json()))
        logger.debug(
            f"Error response for {self.API_URL}/messages/{message_id}: {response}"
        )
        raise MailTMInvalidResponse(
            f"Error response for {self.API_URL}/messages/{message_id}",
            response.json(),
        )

    def delete_message_by_id(
        self,
        message_id: str,
        token: str,
    ) -> bool:
        """
        Delete a specific message by ID.
        
        Args:
            message_id: ID of the message to delete.
            token: Authentication token.
        
        Returns:
            bool: True if deletion was successful.
        
        Raises:
            MailTMInvalidResponse: If the API request fails.
        
        Reference:
            https://docs.mail.tm/#delete-messagesid
        """
        response = self.session.delete(
            f"{self.API_URL}/messages/{message_id}",
            headers={"Authorization": f"Bearer {token}"},
            verify=self.SSL,
        )
        logger.debug(f"Response for {self.API_URL}/messages/{message_id}: {response}")
        if validate_response(response):
            return response.status == 204
        logger.debug(
            f"Error response for {self.API_URL}/messages/{message_id}: {response}"
        )
        raise MailTMInvalidResponse(
            f"Error response for {self.API_URL}/messages/{message_id}",
            response.json(),
        )

    def set_read_message_by_id(
        self,
        message_id: str,
        token: str,
    ) -> bool:
        """
        Mark a message as read.
        
        Args:
            message_id: ID of the message to mark as read.
            token: Authentication token.
        
        Returns:
            bool: True if the message was successfully marked as read.
        
        Raises:
            MailTMInvalidResponse: If the API request fails.
        
        Reference:
            https://docs.mail.tm/#patch-messagesid
        """
        response = self.session.put(
            f"{self.API_URL}/messages/{message_id}/read",
            headers={"Authorization": f"Bearer {token}"},
            verify=self.SSL,
        )
        logger.debug(
            f"Response for {self.API_URL}/messages/{message_id}/read: {response}"
        )
        if validate_response(response):
            return (response.json()).get("seen") == "read"
        logger.debug(
            f"Error response for {self.API_URL}/messages/{message_id}/read: {response}"
        )
        raise MailTMInvalidResponse(
            f"Error response for {self.API_URL}/messages/{message_id}/read",
            response.json(),
        )

    def get_message_source_by_id(
        self,
        message_id: str,
        token: str,
    ) -> MessageSource:
        """
        Get the raw source of a message.
        
        Args:
            message_id: ID of the message to retrieve source for.
            token: Authentication token.
        
        Returns:
            MessageSource: Raw email source object.
        
        Raises:
            MailTMInvalidResponse: If the API request fails.
        
        Reference:
            https://docs.mail.tm/#get-messagesidsource
        """
        response = self.session.get(
            f"{self.API_URL}/messages/{message_id}/source",
            headers={"Authorization": f"Bearer {token}"},
            verify=self.SSL,
        )
        logger.debug(
            f"Response for {self.API_URL}/messages/{message_id}/source: {response}"
        )
        if validate_response(response):
            return MessageSource(**(response.json()))
        logger.debug(
            f"Error response for {self.API_URL}/messages/{message_id}/source: {response}"
        )
        raise MailTMInvalidResponse(
            f"Error response for {self.API_URL}/messages/{message_id}/source",
            response.json(),
        )
