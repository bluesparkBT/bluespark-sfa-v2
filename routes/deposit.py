import traceback
import base64
import copy
from fastapi import Depends, HTTPException, Query, Body
from typing import Annotated, Optional
from fastapi.routing import APIRouter
from sqlmodel import or_, select, Session
from db import get_session
from models.Account import User, Organization
from models.FinanceModule import BankAccount, Deposit, DepositStatus, BankName
from models.viewModel.FinanceView import DepositView as TemplateView, UpdateDepositView as UpdateTemplateView, BankAccountView, UpdateBankAccountView
from utils.auth_util import get_current_user, check_permission
from utils.get_hierarchy import get_organization_ids_by_scope_group
from utils.form_db_fetch import fetch_bank_account_id_and_account, group_bank_accounts_by_bank_name, fetch_organization_id_and_name
from utils.model_converter_util import get_html_types

DepositRouter = dr = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]
UserDep = Annotated[dict, Depends(get_current_user)]

endpoint_name = "deposit" 
db_model = Deposit

endpoint = {
    "get": f"/get-{endpoint_name}s",
    "get_by_id": f"/get-{endpoint_name}",
    "get_form": f"/{endpoint_name}-form/",
    "create": f"/create-{endpoint_name}",
    "update": f"/update-{endpoint_name}",
    "delete": f"/delete-{endpoint_name}",
}

#Update role_modules
role_modules = {   
    "get": ["Finance", "Deposit"],
    "get_form": ["Finance", "Deposit"],
    "create": ["Deposit"],
    "update": ["Finance"],
    "delete": ["Finance"],
}

#CRUD
@dr.get(endpoint['get'])
def get_template(
    session: SessionDep,
    current_user: UserDep,
    tenant: str
):
    try:  
        if not check_permission(
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        # scope group and scop check
        entries_list = None
        if current_user.scope == "managerial_scope":
            entries_list = session.exec(
                select(db_model).where(db_model.organization.in_(organization_ids))
            ).all()
        elif current_user.scope == "personal_scope":
            entries_list = session.exec(
                select(db_model).where(db_model.organization.in_(organization_ids), db_model.sales_representative == current_user.id )
            ).all()  
        if not entries_list:
            raise HTTPException(status_code=404, detail= f" No {endpoint_name} Created")  
          
        deposit_list = []  
        for entry in entries_list:
            sales_rep = session.exec(select(User.full_name).where(User.id == entry.sales_representative)).first()
            bank = session.exec(select(BankAccount.bank_name).where(BankAccount.id == entry.bank)).first()
            org_name = session.exec(select(Organization.name).where(Organization.id == entry.organization)).first()
            temp = {
                "id": entry.id,
                "sales_representative": sales_rep,
                "bank": bank,
                "amount": entry.amount,
                "date": entry.date.strftime("%Y-%m-%d") if entry.date else None,
                "remark": entry.remark,
                "organization": org_name,
                "status": entry.approval_status,
                "deposit_slip": entry.deposit_slip
            }
            if temp not in deposit_list:
                deposit_list.append(temp)
        return deposit_list

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Unable to process your request at the moment.")

@dr.get(endpoint['get_by_id'] + "/{id}")
def get_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    id: int,
):
    """
    Get a deposit by its ID.

    Args:
        session (SessionDep): The database session.
        id (int): The ID of the deposit.

    Returns:
        Deposit: The deposit with the specified ID.
    """
    try:
        if not check_permission(
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        entry = session.exec(
            select(db_model).where(db_model.organization.in_(organization_ids), db_model.id == id)
        ).first()
        
        
        if not entry:
            raise HTTPException(status_code=404, detail="Deposit not found")
        entry_bank_name = session.exec(select(BankAccount.bank_name).where(BankAccount.id == entry.bank)).first()
        entry_account_number = session.exec(select(BankAccount.account).where(BankAccount.id == entry.bank)).first()
        if not entry_account_number:
            entry_account_number = None
            print("Account number not found for the selected deposit")
        return {
                "id":entry.id,
                # "sales_representative": entry.sales_representative,
                "bank": entry_bank_name,
                "account": entry_account_number,
                "branch": entry.branch,
                "amount": entry.amount,
                "remark": entry.remark,
                "date": entry.date,
                # "finance_manager": entry.finance_manager,
                "organization": entry.organization,
                "transaction_number": entry.transaction_number,
                "deposit_slip": entry.deposit_slip
                }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=400, detail="Unable to process your request at the moment."
        )

@dr.get(endpoint['get_form'])
def get_template_form(
    tenant: str,
    session: SessionDep,
    current_user: UserDep,
) :
    """   Retrieves the form structure for creating a new deposit.
    """
    try:
        if not check_permission(
            session, "Create",role_modules['get_form'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            ) 
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        bank_accounts = session.exec(
            select(BankAccount).where(BankAccount.organization.in_(organization_ids))
        ).all()
        #returns bank accounts grouped with the bank name
        accounts = group_bank_accounts_by_bank_name(bank_accounts)
        form_structure = {
            "id":"",
            # "sales_representative":current_user.id,
            "bank": {i.value: i.value for i in BankName},
            "account": fetch_bank_account_id_and_account(session, current_user),
            "branch":"",
            "amount":"",
            "remark":"",
            "date":"",
            "organization" : fetch_organization_id_and_name(session, current_user),
            "transaction_number": "",
            "deposit_slip": ""
        }

        
        html_types = copy.deepcopy(get_html_types('deposit'))
        return {"data": form_structure, "html_types": html_types}
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong") 

@dr.post(endpoint['create'])
def create_template(
    session: SessionDep,
    current_user: UserDep,
    valid: TemplateView,
    tenant: str,
):
    """
    Create a new deposit.

    Args:
        session (SessionDep): The database session.
        deposit (Deposit): The deposit to create.

    Returns:
        Deposit: The created deposit.
    """
    try:
        if not check_permission(
            session, "Create", role_modules['create'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )      
        bank_account = session.exec(select(BankAccount).where(BankAccount.id == valid.account)).first()
        new_entry = db_model(
            # sales_representative = valid.sales_representative
            sales_representative = current_user.id,
            bank = bank_account.id,
            branch = valid.branch,
            amount = valid.amount,
            remark = valid.remark,
            date = valid.date,
            approval_status = DepositStatus.Pending,
            organization = valid.organization,
            transaction_number = valid.transaction_number,
            deposit_slip = valid.deposit_slip

            )
        session.add(new_entry)
        session.commit()
        session.refresh(new_entry)

        return {"message": f"{endpoint_name} created successfully"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Unable to process your request at the moment.")

@dr.put(endpoint['update'])
def update_template(
    session: SessionDep,
    current_user: UserDep,
    valid: UpdateTemplateView,
):
    """
    Update a deposit.
    Args:
        session (SessionDep): The database session.
        deposit (Deposit): The updated deposit.
    Returns:
        Deposit: The updated deposit.
    """
    try:
        if not check_permission(
            session, "Update", role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        current_deposit = session.exec(
            select(Deposit).where(Deposit.id == valid.id, Deposit.organization.in_(organization_ids))
        ).first()
        if not current_deposit:
            raise HTTPException(status_code=404, detail= f"{endpoint_name} not found")
        
        #need improve ment to select bank name an the account number
        
        bank_account = session.exec(select(BankAccount).where(BankAccount.bank_name == valid.bank)).first()
        # current_deposit.sales_representative = valid.sales_representative
        current_deposit.date = valid.date
        current_deposit.bank = bank_account.id
        current_deposit.amount = valid.amount
        current_deposit.branch = valid.branch
        current_deposit.remark = valid.remark

        session.add(current_deposit)
        session.commit()
        session.refresh(current_deposit)
        return current_deposit
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=400, detail="Unable to process your request at the moment."
        )

@dr.put("/approve-deposit/{id}")
async def approve_deposit(
    session: SessionDep,
    current_user: UserDep,
    id: int,
    comment: Optional[str] 
):
    """
    Approve a deposit.

    Args:
        session (SessionDep): The database session.
        id (int): The ID of the deposit to approve.

    Returns:
        Deposit: The approved deposit.
    """
    try:
        if not check_permission(
            session, "Update", role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        deposit = session.exec(select(Deposit).where(Deposit.id == id)).first()
        if not deposit:
            raise HTTPException(status_code=404, detail="Deposit not found")
        
        deposit.approval_status = DepositStatus.Approved
        deposit.finance_manager = current_user.id
        deposit.comment = comment
        session.add(deposit)
        session.commit()
        session.refresh(deposit)
        return deposit
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=400, detail="Unable to process your request at the moment."
        )

@dr.put("/reject-deposit/{id}")
async def reject_deposit(
    session: SessionDep,
    current_user: UserDep,
    id: int,
    comment: str 
):
    """
    Approve a deposit.

    Args:
        session (SessionDep): The database session.
        id (int): The ID of the deposit to approve.

    Returns:
        Deposit: The approved deposit.
    """
    try:
        if not check_permission(
            session, "Update", role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        deposit = session.exec(select(Deposit).where(Deposit.id == id)).first()
        if not deposit:
            raise HTTPException(status_code=404, detail="Deposit not found")
        
        deposit.approval_status = DepositStatus.Rejected
        deposit.finance_manager = current_user.id
        deposit.comment = comment
        session.add(deposit)
        session.commit()
        session.refresh(deposit)
        return deposit
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=400, detail="Unable to process your request at the moment."
        )

@dr.delete(endpoint['delete']+ "/{id}")
def delete_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    id: int
) :
    """
    Delete a deposit by its ID.

    Args:
        session (SessionDep): The database session.
        id (int): The ID of the deposit to delete.

    Returns:
        dict: A message indicating the result of the deletion.
    """
    try:
        # Check permission
        if not check_permission(
            session, "Delete",role_modules['delete'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )

        deposit = session.exec(select(Deposit).where(Deposit.id == id)).first()
        if not deposit:
            raise HTTPException(status_code=404, detail="Deposit not found")
        session.delete(deposit)
        session.commit()
        return {"message": "Deposit deleted successfully"}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Unable to process your request at the moment.")
    
    
        
#Bank account section
@dr.get("/get-bank-accounts")
async def get_bank_accounts(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
):
    try:
        if not check_permission(
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        entries_list = session.exec(
            select(BankAccount).where(BankAccount.organization.in_(organization_ids))
        ).all()

        return entries_list
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to get bank accounts") 

@dr.get("/get-bank-account/{id}")
def get_template(
    session: SessionDep, 
    current_user: UserDep,
    tenant: str,
    id: int,
):
    """
    Get a deposit by its ID.

    Args:
        session (SessionDep): The database session.
        id (int): The ID of the deposit.

    Returns:
        Deposit: The deposit with the specified ID.
    """
    try:
        if not check_permission(
            session, "Read", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        entry = session.exec(
            select(BankAccount).where(BankAccount.organization.in_(organization_ids), BankAccount.id == id)
        ).first()
        
        if not entry:
            raise HTTPException(status_code=404, detail="Bank account not found")
        return {
                "id":entry.id,
                "bank_name": entry.bank_name,
                "account": entry.account,
                "account_holder": entry.account_holder,
                "organization": entry.organization,
                }
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Unable to process your request at the moment."
        )

@dr.get("/bank-accounts/by-bank/")
def get_bank_accounts_by_bank(
    session: SessionDep,
    current_user: UserDep,
    bank_name: BankName = Query(..., description="Bank name"),
    tenant: str = ""
):
    try:
        if not check_permission(
            session, "Read", role_modules['get'], current_user
        ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        accounts = session.exec(
            select(BankAccount)
            .where(BankAccount.bank_name == bank_name)
            .where(BankAccount.organization.in_(organization_ids))
        ).all()
        return [{"id": acc.id, "account": acc.account} for acc in accounts]
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to get bank accounts")


@dr.get("/bank-account-form/")
def get_template_form(
    tenant: str,
    session: SessionDep,
    current_user: UserDep,
) :
    """   Retrieves the form structure for creating a new deposit.
    """
    try:
        if not check_permission(
            session, "Create",role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            ) 
        # organization_ids = get_organization_ids_by_scope_group(session, current_user)
        # bank_accounts = session.exec(
        #     select(BankAccount).where(BankAccount.organization.in_(organization_ids))
        # ).all()
        form_structure = {
            "id":"",
            "bank_name": {i.value: i.value for i in BankName},
            "account": "",
            "account_holder":"",
            "organization" : fetch_organization_id_and_name(session, current_user),
        }
        
        html_types = copy.deepcopy(get_html_types('bank'))
        return {"data": form_structure, "html_types": html_types}
    except HTTPException as http_exc:
        raise http_exc
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Something went wrong") 
    
@dr.post("/create-bank-account/")
def create_bank_account(
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    valid: BankAccountView,
):
    try:
        if not check_permission(
            session, "Create", role_modules['get'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        new_account = BankAccount(
            bank_name=valid.bank_name,
            account=valid.account,
            account_holder=valid.account_holder,
            organization=valid.organization,
        )
        session.add(new_account)
        session.commit()
        session.refresh(new_account)
        return {"message": "Bank account created successfully"}
    
    except HTTPException as http_exc:
        raise http_exc 
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to create bank account")

@dr.put("/update-bank-account/")
def update_bank_account(
    
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    valid: UpdateBankAccountView,
):
    try:
        if not check_permission(
            session, "Update", role_modules['update'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        organization_ids = get_organization_ids_by_scope_group(session, current_user)
        account = session.exec(select(BankAccount).where(BankAccount.id == valid.id, BankAccount.organization.in_(organization_ids))).first()
        if not account:
            raise HTTPException(status_code=404, detail="Bank account not found")
        
        account.bank_name = valid.bank_name
        account.account = valid.account
        account.account_holder = valid.account_holder
        account.organization = valid.organization
        session.add(account)
        session.commit()
        session.refresh(account)
        return {"message": "Bank account updated successfully"}
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to update bank account")

@dr.delete("/delete-bank-account/{id}")
def delete_bank_account(
    
    session: SessionDep,
    current_user: UserDep,
    tenant: str,
    id: int,
):
    try:
        if not check_permission(
            session, "Delete", role_modules['delete'], current_user
            ):
            raise HTTPException(
                status_code=403, detail="You Do not have the required privilege"
            )
        account = session.exec(select(BankAccount).where(BankAccount.id == id)).first()
        if not account:
            raise HTTPException(status_code=404, detail="Bank account not found")
        session.delete(account)
        session.commit()
        return {"message": "Bank account deleted successfully"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to delete bank account")