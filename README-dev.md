Git sha1 computation
--------------------

Document to describe how the git sha1 computation takes place.

### commit/revision

sha1 git commit/revision computation:

    commit `size`\0
    tree `sha1-git-tree-and-subtree-in-plain-hex-string`
    (parent `commit-parent`)
    author `name` <`email`> `date-ts` `date-offset`
    committer `name` <`email`> `date-ts` `date-offset`

    `commit-message`


Notes:
- () denotes optional entry. Indeed, first commit does not contain any parent commit.
- empty line at the end of the commit message
- timestamp example: 1444054085
- date offset for example: +0200

### directory/tree

sha1 git directory/tree computation:

    tree `tree-size`\0
    <file-perm> <file-name>\0<file-sha1-in-20-bytes-string>...<dir-perm> <dir-name>\0<dir-sha1-in-20-bytes-string>...


Notes:
- no newline separator between tree entries
- no empty newline at the end of the tree entries
- tree content header size is the length of the content
- The tree entries are ordered according to bytes in their <name> properties.

Note: Tree entries referencing trees are sorted as if their name have a trailing /
at their end.

Possible permissions are:
- 100644 - file
- 40000  - directory
- 100755 - executable file
- 120000 - symbolink link
- 160000 - git link (relative to submodule)

### content/file

sha1 git content computation:

    blob `blob-size`\0
    `blob-content`

Notes:
- no newline at the end of the blob content

Compress with DEFLATE and compute sha1