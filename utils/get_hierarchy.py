from sqlmodel import select, Session
from fastapi import Depends
from typing import Annotated, List
from models import Account, ScopeGroup, ScopeGroupLink
from db import SECRET_KEY, get_session

from models.Account import Organization


SessionDep = Annotated[Session, Depends(get_session)]

from typing import List
from fastapi import HTTPException

def get_organization_ids_by_scope_group(session, current_user) -> List[int]:
    """
    Get the list of organization IDs linked to the current user's ScopeGroup.

    Args:
        session: The database session.
        current_user: The current user dictionary containing at least 'scope_group_id'.

    Returns:
        List[int]: A list of organization IDs.

    Raises:
        HTTPException: If no ScopeGroup or organizations are found.
    """
    # Fetch the user's scope group object
    user_scope_group = session.exec(
        select(ScopeGroup).where(ScopeGroup.id == current_user.scope_group_id)
    ).first()

    if not user_scope_group:
        raise HTTPException(
            status_code=404, detail="ScopeGroup not found for the current user"
        )

    # Get organization IDs associated with this scope group
    organization_ids = [org.id for org in user_scope_group.organizations]

    if not organization_ids:
        raise HTTPException(
            status_code=404,
            detail="No organizations found for the user's ScopeGroup",
        )

    return organization_ids


def get_child_organization(session: SessionDep, organization_id: int , max_depth = None, children_key="children"):
    """
    Fetch all child organizations (descendants) from the database.
    """
    children = session.exec(
        select(Organization).where(Organization.parent_id == organization_id)
    ).all()

    org = session.exec(select(Organization).where(Organization.id == organization_id)).first()  
    
    if org.parent_id:
        parent_org = session.exec(select(Organization).where(Organization.id == org.parent_id)).first()  
    else:
        parent_org = None
    
    return {
            'id': organization_id,
            'name': "All" if org.parent_id is None else org.organization_name, 
            "owner": org.owner_name,
            "description": org.description,
            "organization_type": org.organization_type,
            "inheritance_group": org.inheritance_group,
            "parent_organization": parent_org.organization_name if parent_org is not None else None,
            "scope_groups": [{"id": sg.id, "scope_name": sg.scope_name} for sg in org.scope_groups],

            children_key: [get_child_organization(session, child.id, max_depth-1 if max_depth is not None else max_depth, children_key) for child in children if (max_depth is None or max_depth > 0)]           
        }
    
def get_heirarchy(session: SessionDep, organization_id: int , max_depth, current_user):
    
    
    user_scope_group = session.exec(
        select(ScopeGroup).where(ScopeGroup.id == current_user.scope_group_id)
    ).first()

    if not user_scope_group:
        raise HTTPException(
            status_code=404, detail="ScopeGroup not found for the current user"
        )
    # Get organization IDs associated with this scope group
    
    organization_ids = [org.id for org in user_scope_group.organizations]
    
    heirarchy = get_child_organization(session, organization_id, max_depth, "hidden")
    
    return heirarchy
    
    
def get_parent_organizations(session: SessionDep, organization_id: int) -> List[int]:
    """
    Fetch all parent organizations recursively (up to the top-level root).
    """
    parents = []
    current_id = organization_id

    while current_id is not None:
        org = session.get(Organization, current_id)
        if not org or org.parent_id is None:
            break
        parents.append(org.parent_id)
        current_id = org.parent_id

    return parents  # List of parent IDs (ordered bottom-up)


#Let’s say you want to return all related organizations with their hierarchy, you could do:
def get_org_with_parents(session: Session, org_ids: List[int]) -> List[Organization]:
    all_ids = set(org_ids)
    for org_id in org_ids:
        parent_ids = get_parent_organizations(session, org_id)
        all_ids.update(parent_ids)
    return session.exec(select(Organization).where(Organization.id.in_(all_ids))).all()



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
