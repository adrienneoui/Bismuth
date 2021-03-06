#issue token: token:issue:worthless:10000
#transfer token: token:transfer:worthless:10

import sqlite3

conn = sqlite3.connect('static/ledger.db')
conn.text_factory = str
c = conn.cursor()

tok = sqlite3.connect('tokens.db')
tok.text_factory = str
t = tok.cursor()
t.execute("CREATE TABLE IF NOT EXISTS transactions (block_height INTEGER, timestamp, token, address, recipient, amount INTEGER)")
tok.commit()


t.execute("SELECT block_height FROM transactions ORDER BY block_height DESC LIMIT 1;")
try:
    token_last_block = int(t.fetchone()[0])
except:
    token_last_block = 0
print("token_last_block", token_last_block)

#print all token issuances
c.execute("SELECT block_height, timestamp, address, recipient, openfield FROM transactions WHERE openfield LIKE ? AND block_height > ? ORDER BY block_height ASC;", ("token:issue" + '%',) + (token_last_block,))
results = c.fetchall()
print (results)

tokens_processed = []

for x in results:
    if x[1] not in tokens_processed:
        block_height = x[0]
        print("block_height", block_height)

        timestamp = x[1]
        print("timestamp", timestamp)

        token = x[4].split(":")[2]
        tokens_processed.append(token)
        print("token", token)

        issued_by = x[3]
        print ("issued_by", issued_by)

        total = x[4].split(":")[3]
        print("total", total)

        t.execute ("INSERT INTO transactions VALUES (?,?,?,?,?,?)", (block_height, timestamp, token, "issued", issued_by, total))
    else:
        print("issuance already processed:", x[1])

tok.commit()
#print all token issuances

print("---")

#print all transfers of a given token
#token = "worthless"
for token in tokens_processed:
    print("processing", token)
    c.execute("SELECT block_height, timestamp, address, recipient, openfield FROM transactions WHERE openfield LIKE ? AND block_height > ? ORDER BY block_height ASC;", ("token:transfer:" + token + ':%' ,)+(token_last_block,))
    results2 = c.fetchall()
    print (results2)

    for r in results2:
        block_height = r[0]
        print("block_height", block_height)

        timestamp = r[1]
        print("timestamp", timestamp)

        token = r[4].split(":")[2]
        print("token", token, "operation")

        sender = r[2]
        print ("transfer_from", sender)

        recipient = r[3]
        print ("transfer_to", recipient)

        transfer_amount = int(r[4].split(":")[3])
        print ("transfer_amount",transfer_amount)

        #calculate balances
        t.execute("SELECT sum(amount) FROM transactions WHERE recipient = ? AND block_height < ? AND token = ?", (sender,) + (block_height,) + (token,))
        try:
            credit_sender = int(t.fetchone()[0])
        except:
            credit_sender = 0
        print("credit_sender", credit_sender)

        t.execute("SELECT sum(amount) FROM transactions WHERE address = ? AND block_height <= ? AND token = ?", (sender,) + (block_height,) + (token,))
        try:
            debit_sender = int(t.fetchone()[0])
        except:
            debit_sender = 0
        print("debit_sender", debit_sender)
        #calculate balances

        #print all token transfers
        balance_sender = credit_sender - debit_sender
        print ("balance_sender", balance_sender)

        if balance_sender - transfer_amount> 0 or transfer_amount < 0:
            t.execute("INSERT INTO transactions VALUES (?,?,?,?,?,?)", (block_height, timestamp, token, sender, recipient, transfer_amount))
        else:
            print ("invalid transaction by", sender)
        print("---")

    tok.commit()

conn.close()