.. image:: https://github.com/MatthiasValvekens/python-pae/workflows/pytest/badge.svg
   :target: https://github.com/MatthiasValvekens/python-pae

.. image:: https://codecov.io/gh/MatthiasValvekens/python-pae/branch/master/graph/badge.svg?token=XPRS49L0X6
   :target: https://codecov.io/gh/MatthiasValvekens/python-pae

Pre-authentication encoding in Python
=====================================

This minimal library offers an implementation of (a variant of)
`PASETO <https://github.com/paragonie/paseto>`_'s pre-authentication encoding
(PAE) scheme in Python, with some extra tools to handle data types other than lists of byte arrays.


Why use pre-authentication encoding?
------------------------------------

When passing around data between services, it's often necessary to authenticate and validate
encoded messages. When those messages are flat byte streams, that's easy enough. However,
when authenticating complex data structures with many fields (some of which may be optional or
perhaps exempt from authentication), the input data must first be serialised before it can
be passed on to the authentication mechanism.
The interchange formats that are commonly used to hold such complex data in transit between web
services (e.g. JSON or HTTP query parameters) are poorly suited for this task.

Naively concatenating all inputs before authentication is typically not a good idea, since
it can lead to vulnerabilities through
`length extension attacks <https://en.wikipedia.org/wiki/Length_extension_attack>`_
or other types of `canonicalisation attacks <https://soatok.blog/2021/07/30/canonicalization-attacks-against-macs-and-signatures/>`_.

Pre-authentication encoding (PAE) can help you protect yourself against a large class of such
exploits, by explicitly making the *number* of data fields and the *length* of each field part of
the data covered by the MAC/signature.

PAE can be used explicitly or implicitly. In the explicit case, PAE serves as both the interchange
format and the authentication format.
In the implicit case, PAE is used to preprocess data in some other container format before
signing/authenticating it, but its output isn't transmitted directly.

A typical use case would be a ``signature`` entry in a JSON object that authenticates one or more
of its sibling entries. The signature value would then be computed by applying PAE to the
authenticated sibling entries, and passing the result to the signature algorithm.


Requirements
------------

Requires Python 3.7 or later.


Notes
-----

This library has no runtime dependencies, and does not supply any cryptographic operations.
Its main purpose is to preprocess complex data structures before authenticating their contents
using a MAC or digital signature. The actual authentication mechanism is out of scope, and left
to the caller.
This library also does not offer any abstractions to handle token expiration, revocation,
algorithm selection or anything of the sort.


Stability
---------

Experimental.