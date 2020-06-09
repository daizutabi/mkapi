# Ordering Members in Different Files

<style type="text/css">
<!--
.mkapi-node {
  border: 2px dashed #88AA88;
}
-->
</style>

{{ # cache:clear }}

Class members that are defined in different files are sorted by a key of (minus of *source file index*, line number).

#File appendix/member_order_base.py {%=/examples/appendix/member_order_base.py%}

#File appendix/member_order_sub.py {%=/examples/appendix/member_order_sub.py%}

![mkapi](appendix.member_order_base.A)

![mkapi](appendix.member_order_sub.B)

![mkapi](appendix.member_order_sub.C)
