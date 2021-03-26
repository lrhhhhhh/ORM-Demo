### 前言
**这是一个玩具ORM**，没多大实用价值，很多细节也并没有考虑。

### 实现思路
ORM从一个非常高层次的抽象来看，就只是将数据库表记录转换为OOP中的对象，或者将对象转换为数据库表记录。除此之外，还有大量对数据库表单的操作封装在ORM中
这个简单demo的实现思路大致如下：
- 利用metaclass实现记录表单字段的映射关系
- 表单字段利用descriptor实现，设计了`validate()`接口，可以对每个字段进行检测
- 在表单的基类`Model`中进行各样的操作
- 保证读取出来的数据被实例化为对象

### 版本
有两个tag，其中:
- `orm`的实现是基于`descriptor`和`metaclass`的，
- `orm_implemented_by_descriptor_only`的实现仅仅基于`descriptor`
