from sqlalchemy.ext.automap import automap_base
from DMP_API.settings import engine


# Reflect existing database into SqlAlchemy models
Base = automap_base()
Base.prepare(engine.engine, reflect=True)


# Grab the models from Base class
DMP_USERS = Base.classes.dmp_users
USER_SESSION = Base.classes.user_session

Customer = Base.classes.customer
Supplier = Base.classes.supplier
SupplierCustomerConnection = Base.classes.supplier_customer_connection
Pricebook = Base.classes.pricebook
PricebookConnection = Base.classes.pricebook_connection
