# CHANGELOG

#### 0.3.3

* Reverse field's name are now correctly fetched

#### 0.3.2

* Joins now correctly account for nullable foreign key

#### 0.3.1

* Minor fix


### 0.3.0

* Instead of calling commands in a specific order, each field/value pair of the
query string call the commands with a regex matching the field. The main
consequence of this change is that query argument's order now matter.

* Added `c:distinct` command as well as `distinct` argument for for `c:join`. A
new function called `dcount` (to make distinct count) has been added for
`c:aggregate` and `c:annotate`.

#### 0.2.1

* Added `serialize()` method to serialize a model instance in the same format
  as a `GenericQuery`'s row.

### 0.2.0

* Now can allow only specific field for each Model, or can use django's permission system

#### 0.1.1 & 0.1.2

* Added missing MANIFEST.in

### 0.1.0

* Initial release
