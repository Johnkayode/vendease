import typing

def amount_to_denominations(amount: int) -> typing.List[int]:
    """
    Convert change to coin denominations.
    
    Args:
        amount: Amount in cents to convert to denominations
        
    Returns:
        List of coins (in denominations of 5, 10, 20, 50 and 100 cents)

    """
    coins = [100, 50, 20, 10, 5]
    change = []
    
    for coin in coins:
        count = amount // coin
        change.extend([coin] * count)
        amount -= count * coin
    return change