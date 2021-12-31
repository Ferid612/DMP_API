from sqlalchemy.ext.automap import automap_base
from DMP_API.settings import engine
print("i am working*****************************************************************2222")

# Reflect existing database into SqlAlchemy models
a=1
if a==1:
    
    Base = automap_base()
    Base.prepare(engine.engine, reflect=True)


    # Grab the models from Base class
    DMP_USERS = Base.classes.dmp_users
    USER_SESSION = Base.classes.user_session
    USER_SESSION_WITH_DATA = Base.classes.user_session_with_data

    Customer = Base.classes.customer
    Supplier = Base.classes.supplier
    SupplierCustomerConnection = Base.classes.supplier_customer_connection
    Pricebook = Base.classes.pricebook
    PricebookConnection = Base.classes.pricebook_connection
    a=2
else:
    Base = ""
    # Base.prepare(engine.engine, reflect=True)


    # Grab the models from Base class
    DMP_USERS = ""
    USER_SESSION = ""
    USER_SESSION_WITH_DATA = ""

    Customer = ""
    Supplier = ""
    SupplierCustomerConnection = ""
    Pricebook = ""
    PricebookConnection = ""