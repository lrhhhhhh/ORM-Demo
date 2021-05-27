## SimpleORM
SimpleORM is a simple Object-Relational Mapper(ORM) 
implemented by Python's technology which named metaclass and descriptor

SimpleORM是基于mysql数据库设计的一个简单的对象关系映射框架，API风格和flask-sqlalchemy类似，但并没有参考其具体实现。
纯粹的看API猜如何实现，这是一个为了造轮子而造的轮子。

## Features
- 创建（Create）：创建数据库、数据表、数据表行记录 
- 更新（Update）：更新一个或多个行记录
- 检索（Retrieve）: 查找满足条件的表单记录 
- 删除（Delete）: 删除满足条件的一个或多个行记录，删除数据表、删除数据库
- session：可以将操作后的不同表单的数据提交至session中，然后一次性提交给数据库。session是线程安全的。
- 表单字段（Field）：提供丰富的表单字段包括String，Integer，Double，Boolean，Date，DateTime，Timestamp 
- 表单字段验证器（Validator）：提供功能丰富的验证器，方便对各种表单字段进行验证


## 安装依赖
SimpleORM仅仅依赖`pymysql`, 请先安装
```shell
pip install pymysql
```


## 快速开始
以下例子均来自`example/example.py`。

### 配置与初始化ORM对象
```python
from SimpleORM import SimpleORM
db = SimpleORM(
    user='root',
    password='123456',
    database='test_orm',
    host='localhost',
    port=3306,
)
```
请根据自己情况填写用户名、密码、端口、数据库名

### 定义数据表
```python
class Student(db.Model):
    table_name = 'students'
    uid = Integer(primary_key=True, auto_increment=True)
    age = Integer(primary_key=False)
    height = Double(primary_key=False, m=5, d=3)
    username = String(primary_key=False, max_length=128)
    sex = Boolean(default=False)
    birthday = Date()
    last_seen = DateTime()
    timestamp = TimeStamp()
```

### 创建数据表
```python
db.create_all()
```

### 插入数据

```python
s1 = Student(
    username=f'lrh',
    age=24,
    height=1.75,
    sex=True,
    birthday='1999-09-19',
    last_seen=datetime.datetime.now(),
    timestamp=int(time.time())
)
db.session.add(s1)
db.session.commit()
```

### 获取当前session中和数据库的连接
```python
current_ctx_conn = db.session.connection
```

### 查看数据表全部数据
```python
Student.query(bind=current_ctx_conn).select_all()
```


### 查找数据
```python
s = Student.query().filter_by(username='lrh')[0]
print(s)
```

### 修改数据
```python
s.username = 'mao'
db.session.add(s)
db.session.commit()
```

### 删除数据
```python
db.session.remove(s)
db.session.commit()
```


## 实现思路
1. ORM从一个非常高层次的抽象来看，就只是将数据库表记录转换为OOP中的对象，或者将对象转换为数据库表记录。除此之外，还有大量对数据库表单的操作封装在ORM中。这个简单demo的实现思路大致如下：
- 利用metaclass实现记录表单字段的映射关系
- 提供接口，使得从数据库读取出来的数据被实例化为继承了Model类的表单类的实例
  
2. 数据库连接问题
- 一些常见的框架提供这样的功能:`User.query.filter_by()`, 这意味每一个query都有一个连接，而每一个User（注意是类）都包含着一个query，
  这就意味着`connection`到处乱传，到处生成。
- 本框架在设计时就饱受这个问题影响，我采用的解决策略是：
    - 利用session：我们操作数据库时，至少有一个连接，那就是session中的连接，当我们使用query进行查询时绑定这个连接
    
3. 如何设计session？
- session涉及到线程安全问题，多个线程使用同一个session时，可能会造成问题。
- 采用`ContextVar`解决线程安全问题（其实也是协程安全）
- session在初始化时，为当前线程（主线程）实例化一个连接存放在当前上下文中，
  若其他线程在使用session时想获取连接，因为当前上下文没有连接，则会触发新建连接

4. 对数据库的操作（CURD）放在哪里？
- 基于我的设计策略：
    - Model只做表单字段和数据库字段的映射，
    - **表单类中不包含数据库连接**，所以我把对数据库的操作全部放到了有数据库连接的`session`中
- session提供create、update、insert、select、delete
- session为什么不提供查询：我把查询操作抽象为Query类，见下文。

5. Query类设计思路
- 基于类似于`User.query.filter_by()`这样的使用习惯，意味这每个数据表类都绑定了一个query， 
但我们的数据表基本逻辑实现是在数据表基类`Model`中实现的，而query的构造需要对应数据表子类的引用， 
这意味着不能将query设置成Model类的类变量
- 我同理采用了描述器实现query，当具体的数据表类，如`User`，它执行`User.query`时将新建一个没有连接的query类，这样做我们能获得
`User`类的引用，从而获取其各种信息（如表单各个字段）。利用描述器可以很好的完成这一点，


## 开发日志
一、session.add(record)时如何判断record是insert还是update：
1. 从数据库读取出来构造**记录实例**时设置一个标志`read_from_db`，表明这个记录是从数据库读出来的
2. 若这样的记录进入了session.add()里，则可以认定为是update操作。
   按这样的逻辑，不是从数据库中读取构造的实例将不能进行update操作
3. 想要解决这个问题有一个简单的方法，那就是把当前add()的逻辑拆分成`insert()`和`update()`
两个子逻辑。我没有这么做的原因是，使用add()符合习惯。
4. 即使拆分了也要同样要面对update如何进行的问题，详情参见开发日志中的**第五点**
   
二、session如何一次更新多条记录：
1. 暂时没有一个通用的办法能一次更新多条记录，原因为：
    - (a) `insert on duplicate key update`执行`update`而不是`insert`的前提是`UNIQUE索引`或者`PRIMARY KEY`重复，
    这意味着不满足条件时，执行的是insert操作。
2. ~~对有primary key和unique的表单记录采用`insert on duplicate key update`的方式插入~~
3. ~~对不满足第2点的记录执行单次update。新的问题来了，没有unique和primary key修饰的记录如何进行update？~~
4. 现在的策略：每一条记录执行一次更新

三、session如何一次插入多条记录：
1. 考虑到顺序问题，**不应该**将操作顺序上不连续的、相同表单的待插入记录组合在一起执行一次插入，应该对每个记录单独执行插入操作。
2. 操作顺序上连续、且都是同一个表单的待插入记录可以组合在一起，一次插入
3. 现在的策略：每一条记录执行一次插入

四、session的add()操作和remove()操作顺序是否有影响？
1. 有影响，必须按照用户提交的顺序进行insert、update和delete，所以session中所有的操作都必须逐个进行。
2. 这意味着`session.commit()`的顺序按照`session.add()`和`session.remove()`的顺序严格执行
3. 用户需要保证操作顺序合法、保证每个操作合法


五、ORM如何执行update操作？（分为两种情形）

- (I)被修改的记录是从数据库读取出来，由ORM生成的类对象。  
   - 当前策略：  
        - 1.行记录有primary key，直接用primary key字段查询与更新  
        - 2.数据表没有primary key时如何执行更新？（todo）  
        - 2.1 保证执行update的实例是从数据库读取出来并生成的  
        - 2.2 因为是update操作，所以是从数据库中读出来的，这样我们可以记录从数据库读出来后哪些字段发生了改变，用不变的字段做条件去查询。
- （II）被修改的记录是用户自己构造的，满足表定义，**但可能不满足数据库表的实际内容**  
    - 用户构造的记录，可能和数据库内容有冲突  
    - 当有primary key时候，用primary key进行update  
    - 当没有primary key时，**无法解决**， 理由如下：  
        - 1.不知道使用什么作为条件进行查询  
        - 2.若用户要提交自定义的记录（不是从数据库读取的记录），则需要**显式**提供查询的条件，但这一点会破坏设计的接口  


    