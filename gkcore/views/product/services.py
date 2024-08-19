from sqlalchemy import and_, select
from gkcore import eng
from gkcore.models.gkdb import product


def check_duplicate_item_name(item_name, orgcode, current_item_code=None):
    """Check for entries with same name. Requires `item_name` and `orgcode`.
    `current_item_code` is required to exclude the current item from the filter while
    item name is being updated.
    """
    with eng.connect() as conn:
        statement = select([product.c.productcode]).where(
            and_(
                product.c.productdesc == item_name,
                product.c.orgcode == orgcode,
            )
        )
        if current_item_code:
            statement = statement.where(
                product.c.productcode != current_item_code,
            )
        product_results = conn.execute(statement)
        if product_results.rowcount:
            raise ValueError("This name is already used.")
