import hashlib

def get_merkle_root(transactions):
    transaction_hashes = [hashlib.sha256(f"{str(tx)}".encode()) for tx in transactions]
    n_transactions = len(transaction_hashes)

    # If no transactions, return empty hash
    if n_transactions == 0:
        return hashlib.sha256(b'').hexdigest()

    # Construct merkle tree
    nodes = transaction_hashes
    while len(nodes) > 1:
        if len(nodes) % 2 != 0:
            nodes.append(nodes[-1])
        nodes = [hashlib.sha256(f"{nodes[i]}{nodes[i+1]}".encode()).digest() for i in range(0, len(nodes), 2)]
    
    return f"{nodes[0]}".encode().hex()
