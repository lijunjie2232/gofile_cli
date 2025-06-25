import json
import logging

from requests import Session

from gofile_cli.entity import (
    Account,
    Token,
    Domains,
    Domain,
    Messages,
    OneMessage,
    MessageSource,
    MailTMInvalidResponse,
)
from gofile_cli.utils import random_string, validate_response

logger = logging.getLogger("mailtm")


class MailTM:
    API_URL = "https://api.mail.tm"
    SSL = False

    def __init__(
        self,
        session: Session = None,
    ):
        self.session = session or Session()

    def get_account_token(
        self,
        address: str,
        password: str,
    ) -> Token:
        """
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

    def get_account(
        self,
        address: str = None,
        password: str = None,
    ) -> Account:
        """
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
        mail: Account = None,
        account_id: str = "",
        token: str = "",
    ) -> bool:
        """
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
        token: str,
    ) -> Account:
        """
        https://docs.mail.tm/#get-me
        """
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
        account: Account = None,
        token: str = "",
        page: int = 1,
    ) -> Messages:
        """
        https://docs.mail.tm/#get-messages
        """
        assert account or token, "account or token must be provided"
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
        account: Account = None,
        token: str = "",
    ) -> OneMessage:
        """
        https://docs.mail.tm/#get-messagesid
        """
        assert account or token, "account or token must be provided"
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
            return (response.json())["seen"] == "read"
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
