# History

## 0.4.4 (2020-02-08)

* Fixed table storage for insert-only keyless tables, like tradeBin. Uses attributes from partial message instead of the keys list.

## 0.4.2 (2020-02-05)

* Relaxed python dependency to 3.6

## 0.4.1 (2020-02-05)

* Checks network argument to BitMEXWebsocket init method is valid.
* storage.insert() method allows storage to be patched externally.

## 0.4.0 (2020-02-03)

* Big refactoring.
* Handles subscriptions individually per channel.
* Data storage uses sorted containers for search efficiency.

## 0.2.5 (2019-11-25)

* Documentation fixes.

## 0.2.4 (2019-11-24)

* Added documentation.

## 0.2.1 (2019-11-24)

* First release on PyPI.
