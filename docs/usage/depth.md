# Depth Limitation

<style type="text/css">
<!--
.mkapi-node-depth-0 {
  border: 2px dashed #88AA88;
}
-->
</style>

!!! warning
    The feature of depth limitatoin will be removed in the future version in favor of "[Page mode](../usage/page.md)".

By default, MkApi searchs objects to unlimited depth. You can control the depth by adding ":(depth)" to the object name.

~~~markdown
![mkapi][numpy_style:0]
~~~

![mkapi](numpy_style:0)


~~~markdown
![mkapi][numpy_style:1]
~~~

![mkapi](numpy_style:1)
