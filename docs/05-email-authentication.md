# Email Authentication: SPF, DKIM, and DMARC

## The Spoofing Problem

SMTP has no built-in sender verification. Anyone can claim to be `ceo@yourcompany.com` in the `MAIL FROM` command. This makes email spoofing trivial and is the basis of most phishing attacks.

Three mechanisms were developed to fix this: SPF, DKIM, and DMARC. They work together as layers of authentication.

## SPF (Sender Policy Framework)

**What it does**: Declares which servers are allowed to send email for a domain.

**How it works**: The domain owner publishes a TXT record in DNS listing authorized sending IP addresses.

```
$ dig TXT google.com
google.com.  TXT  "v=spf1 include:_spf.google.com ~all"
```

When a receiving server gets an email claiming to be from `@google.com`:
1. Look up the SPF record for `google.com`
2. Check if the sending server's IP is in the authorized list
3. If not, the email fails SPF

SPF qualifiers:
- `+all` -- pass everything (defeats the purpose)
- `-all` -- hard fail: reject unauthorized senders
- `~all` -- soft fail: accept but mark suspicious
- `?all` -- neutral: no policy

**Limitation**: SPF checks the **envelope sender** (MAIL FROM), not the header From that users see. And it breaks when email is forwarded, because the forwarding server's IP isn't in the original domain's SPF record.

## DKIM (DomainKeys Identified Mail)

**What it does**: Cryptographically signs email headers and body so recipients can verify the message wasn't tampered with.

**How it works**:
1. The sending server has a private key
2. It signs selected headers (From, Subject, Date, etc.) and the body hash
3. The signature is added as a `DKIM-Signature` header
4. The public key is published in DNS as a TXT record

```
DKIM-Signature: v=1; a=rsa-sha256; d=example.com; s=selector1;
  h=from:to:subject:date;
  bh=base64_body_hash;
  b=base64_signature
```

The receiving server:
1. Extracts the domain (`d=`) and selector (`s=`) from the signature
2. Looks up `selector1._domainkey.example.com` in DNS to get the public key
3. Verifies the signature against the headers and body
4. If valid, the message is authentically from that domain and unmodified

**Advantage over SPF**: DKIM survives forwarding because the signature travels with the message.

## DMARC (Domain-based Message Authentication, Reporting, and Conformance)

**What it does**: Tells receiving servers what to do when SPF and DKIM fail, and provides reporting.

**How it works**: Published as a DNS TXT record at `_dmarc.example.com`:

```
$ dig TXT _dmarc.gmail.com
_dmarc.gmail.com.  TXT  "v=DMARC1; p=none; sp=quarantine; rua=mailto:dmarc@gmail.com"
```

DMARC adds a critical concept: **alignment**. It checks that the domain in the header From matches the domain verified by SPF or DKIM.

DMARC policies:
- `p=none` -- monitor only, don't enforce (reporting mode)
- `p=quarantine` -- mark failures as spam
- `p=reject` -- reject failures outright

## How They Work Together

```
Incoming email claims: From: ceo@company.com

Step 1 - SPF Check:
  Is the sending IP authorized by company.com's SPF record?
  [PASS/FAIL]

Step 2 - DKIM Check:
  Does the DKIM signature verify with company.com's public key?
  [PASS/FAIL]

Step 3 - DMARC Check:
  Does the header From domain align with SPF or DKIM domain?
  [PASS/FAIL]

  If FAIL: apply DMARC policy (none/quarantine/reject)
```

An email passes DMARC if **either** SPF or DKIM passes with alignment.

## Reading Email Headers

You can see authentication results in email headers. Look for the `Authentication-Results` header:

```
Authentication-Results: mx.google.com;
  dkim=pass header.d=example.com;
  spf=pass (google.com: domain of user@example.com designates 1.2.3.4 as permitted sender);
  dmarc=pass (p=REJECT) header.from=example.com
```

This tells you:
- DKIM: passed, signed by example.com
- SPF: passed, the sending IP is authorized
- DMARC: passed, policy is REJECT (strict)

## Why Gmail Requires These

Gmail and other major providers use SPF, DKIM, and DMARC to decide:
- Should this email go to Inbox, Spam, or be rejected?
- Should we show a warning to the user?

Since February 2024, Gmail requires bulk senders to have:
- Valid SPF and DKIM records
- A DMARC policy (at minimum `p=none`)
- One-click unsubscribe for marketing emails

## Relevance to This Project

When this email assistant sends email via SMTP, the authentication is handled by your email provider:
- Gmail signs outgoing mail with DKIM automatically
- Gmail's SPF record authorizes its own servers
- Your sent email will pass authentication checks at the recipient's end

When reading email, the authentication results in the headers tell you whether an email is legitimately from who it claims to be -- useful context for the AI assistant when evaluating trustworthiness.
