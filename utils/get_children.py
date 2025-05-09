from sqlmodel import select, Session
from fastapi import Depends
from typing import Annotated, List
from models import Account
from db import SECRET_KEY, get_session

from models.MultiTenant import Organization


SessionDep = Annotated[Session, Depends(get_session)]


def get_child_organization(session: SessionDep, organization_id: int):
    """
    Fetch all child organizations from the database.
    """
    # TODO check for circular using a dict (dijkstra)
    queue = []
    queue.append(organization_id)

    organization = []
    while queue != []:
        org = queue.pop(0)
        organization.append(org)
        db_org = session.exec(
            select(Organization.id).where(Organization.parent_organization == org)
        ).all()
        queue.extend(db_org)

    return organization


def get_child_employee(session: SessionDep, employee_id: int):
    """
    Fetch all subordinate employees from the database.
    """
    # TODO check for circular using a dict (dijkstra)
    queue = []
    queue.append(employee_id)

    employee = []
    while queue != []:
        emp = queue.pop(0)
        employee.append(emp)
        db_emp = session.exec(
            select(Account.id).where(Account.manager == employee_id)
        ).all()
        queue.extend(db_emp)

    return employee
