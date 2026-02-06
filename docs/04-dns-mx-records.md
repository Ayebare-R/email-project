# DNS and MX Records

## The Problem

When you send email to `alice@example.com`, how does your mail server know which server to deliver it to? The answer is DNS -- specifically, MX (Mail Exchanger) records.

## Quick DNS Refresher

DNS (Domain Name System) translates domain names to IP addresses and other data. It's a distributed hierarchical database:

```
You query: "What's the IP for example.com?"
                |
     [Your DNS resolver]
          |         \
  [Root servers]  [.com TLD servers]  [example.com authoritative server]
                                              |
                                    A record: 93.184.216.34
```

DNS has multiple record types:
- **A**: Domain -> IPv4 address
- **AAAA**: Domain -> IPv6 address
- **MX**: Domain -> mail server hostname + priority
- **CNAME**: Domain -> another domain (alias)
- **TXT**: Arbitrary text (used for SPF, DKIM, DMARC)
- **NS**: Domain -> authoritative nameserver

## MX Records

MX (Mail Exchanger) records tell sending mail servers where to deliver email for a domain.

An MX record has two parts:
- **Priority** (lower = preferred)
- **Mail server hostname**

Example for gmail.com:
```
$ dig MX gmail.com

gmail.com.    MX    5  gmail-smtp-in.l.google.com.
gmail.com.    MX   10  alt1.gmail-smtp-in.l.google.com.
gmail.com.    MX   20  alt2.gmail-smtp-in.l.google.com.
gmail.com.    MX   30  alt3.gmail-smtp-in.l.google.com.
gmail.com.    MX   40  alt4.gmail-smtp-in.l.google.com.
```

When a mail server wants to deliver to `alice@gmail.com`:
1. Query DNS for `MX gmail.com`
2. Get the list of MX records
3. Try the lowest priority first (5 -> `gmail-smtp-in.l.google.com`)
4. Resolve that hostname to an IP address (A/AAAA record)
5. Connect via SMTP on port 25
6. If that server is down, try priority 10, then 20, etc.

## The Full Delivery Flow

```
send to alice@example.com
         |
         v
1. Query: dig MX example.com
   Result: 10 mail.example.com
         |
         v
2. Query: dig A mail.example.com
   Result: 203.0.113.50
         |
         v
3. Connect: SMTP to 203.0.113.50:25
         |
         v
4. EHLO, MAIL FROM, RCPT TO, DATA...
         |
         v
5. Remote server accepts -> delivered
```

## Priority and Failover

MX priorities enable redundancy:
- Priority 10 is tried first (primary server)
- If it's down, try priority 20 (backup)
- If that's down, try priority 30, etc.

Sending servers typically retry for up to 5 days before giving up and sending a bounce (non-delivery report) back to the sender.

## What If There Are No MX Records?

RFC 5321 defines a fallback: if no MX records exist, the sending server tries the domain's A record directly. So if `example.com` has no MX but has an A record pointing to `203.0.113.50`, the sending server will try SMTP delivery to that IP.

This is a fallback mechanism -- properly configured email domains should always have MX records.

## TTL and Caching

DNS records have a TTL (Time To Live) -- how long resolvers should cache the answer before re-querying. MX records typically have TTLs of 1-24 hours.

This means:
- Changes to MX records don't take effect instantly
- During migration, you might need to keep old and new servers running until the TTL expires
- Lower TTL = faster propagation but more DNS queries

## Trying It Yourself

You can query MX records from the command line:

```bash
# Using dig
dig MX gmail.com

# Using nslookup
nslookup -type=MX gmail.com

# Using Python
import dns.resolver  # pip install dnspython
answers = dns.resolver.resolve('gmail.com', 'MX')
for rdata in answers:
    print(f"Priority {rdata.preference}: {rdata.exchange}")
```

## How This Relates to the Project

When you configure `imap.gmail.com` and `smtp.gmail.com` in this project:
- `imap.gmail.com` is Gmail's IMAP server -- you connect to it directly to read email
- `smtp.gmail.com` is Gmail's submission server -- you submit outgoing email to it
- Gmail's servers then use MX lookups to route your outgoing email to the recipient's domain

You don't need to do MX lookups yourself -- your email provider handles the routing. But understanding MX records helps you understand the full pipeline.
