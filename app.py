from email.policy import default
from flask import Flask, flash, redirect, send_file, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
import json
from datetime import date, datetime
from flask_mysqldb import MySQL
from flask_login import LoginManager, login_required, login_user, logout_user, UserMixin
from json import load
from typing import Dict, Optional



app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
users: Dict[str, "User"] = {}


class User(UserMixin):
    def __init__(self, id: str, username: str, password: str):
        self.id = id
        self.username = username
        self.password = password

    @staticmethod
    def get(username: str) -> Optional["User"]:
        return users.get(username)


with open("config.json") as file:
    data = load(file)
    for key in data:
        users[key] = User(
            id=key,
            username=data[key]["username"],
            password=data[key]["password"],
        )

app.config['SECRET_KEY'] = 'mynameiskhan'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'anas2002'
app.config['MYSQL_DB'] = 'dbms_project'
mysql = MySQL(app)


@login_manager.user_loader
def load_user(user_id) -> Optional[User]:
    return User.get(user_id)


@app.route("/logout", methods=['POST', 'GET'])
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/", methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        uname = request.form['name']
        pw = request.form['pw']
        user = User.get('1')
        if user.password == pw and user.username == uname:
            login_user(user)
            flash("Successfully logged in!")
            return redirect(url_for("dashboard"))
    return render_template('login.html')


@app.route("/dash", methods=['POST', 'GET'])
@login_required
def dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(cust_id) FROM customer")
    counts_cust = cur.fetchall()
    cont = counts_cust[0][0]
    mysql.connection.commit()
    cur.execute("SELECT COUNT(order_id) FROM orders")
    counts_order = cur.fetchall()
    cont_order = counts_order[0][0]
    cur.execute("SELECT SUM(total_bill) FROM orders")
    total_earning = cur.fetchall()
    earn = total_earning[0][0]
    mysql.connection.commit()
    cur.execute("""SELECT prod_id from prod_sell,orders
            where orders.order_date BETWEEN date_sub(now(), interval 1 week) AND date_add(now(), 
            interval 7 day) group by (prod_id) order by count(prod_id) DESC LIMIT 1
    """)
    most_freq_one = cur.fetchall()
    mysql.connection.commit()
    mfo = most_freq_one[0][0]
    cur.execute("select pname from products where prod_id=%s", (mfo,))
    mfo = cur.fetchall()
    mfo = mfo[0][0]
    try:
        cur.execute("""SELECT prod_id from prod_sell
                        group by (prod_id)
                        order by count(prod_id) DESC 
                        LIMIT 3;
        """)

        most_freq_three = cur.fetchall()
    except:
        flash("Products Not Present")    
    lst=[]
    for i in range(len(most_freq_three)):
        cur.execute("select pname from products where prod_id=%s",(most_freq_three[i][0],))
        lst.append(cur.fetchall()[0][0])
    cur = mysql.connection.cursor()
    cur.execute("""
            SELECT  
            COUNT(order_id) 
            FROM orders
            GROUP BY WEEK(order_date)
            ORDER BY WEEK(order_date)""")
    myData = cur.fetchall()
    i = 1
    dict = {}
    for order in myData:
        dict[str(i)] = str(order[0])
        i += 1
    mysql.connection.commit()
    cur.close()
    cur = mysql.connection.cursor()
    cur.execute("""
        select pname,count(prod_sell.prod_id) as prod_sales
        from products 
        inner join  prod_sell
        on products.prod_id=prod_sell.prod_id
        group by prod_sell.prod_id;
    """)
    profit_sales = cur.fetchall()
    abc = {}
    for ps in profit_sales:
        abc[ps[0]] = ps[1]

    return render_template('dashboard.html', cont=cont, admin=data["1"]['username'], cont_order=cont_order, earn=earn, graph=dict,lst=lst,mfo=mfo, ps=abc)



@app.route("/order/<string:prod_id>", methods=['POST', 'GET'])
def order(prod_id):
    if request.method == "POST" and int(request.form[prod_id]) > 0:
        qty = request.form[prod_id]
        cur = mysql.connection.cursor()
        cur.execute(
            " SELECT total_price FROM PRODUCTS WHERE prod_id=%s", (prod_id,))
        total_price = cur.fetchall()
        tp=total_price[0][0]
        tp = int(tp)
        total = int(qty)*tp
        cur.execute("SELECT MAX(order_id) FROM ORDERS")
        new_order = cur.fetchall()
        newo = new_order[0][0]
        cur.execute("SELECT prod_id from prod_sell where (order_id=%s AND prod_id=%s)",(newo,prod_id))
        check=cur.fetchall()
        if len(check)>0:
            cur.execute("SELECT qty from prod_sell where (order_id=%s AND prod_id=%s)",(newo,prod_id))
            newqty=cur.fetchall()
            newqty=int(qty)+int(newqty[0][0])
            total=newqty*tp
            cur.execute("""UPDATE prod_sell SET qty=%s,total=%s WHERE (order_id=%s AND prod_id=%s) """,(newqty,total,newo,prod_id))
            mysql.connection.commit()
        else:    
            try:
                cur.execute("INSERT INTO prod_sell (order_id,prod_id,qty,total) VALUES (%s,%s,%s,%s)",
                            (newo, prod_id, qty, total))
                mysql.connection.commit()
            except:
                flash('Already Added')    
    else:
        flash('Products Not added')
    return redirect(url_for('orderp'))


@app.route("/add_emp", methods=['POST', 'GET'])
def add_emp():
    if request.method == "POST":
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        sal = request.form['sal']
        job = request.form['job']
        shift = request.form['shift']
        ph_no = request.form['ph_no']
        address = request.form['addr']
        city = request.form['city']
        id = request.form['id']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO employee (fname,lname, email,sal,job,shift,ph_no,emp_id) VALUES (%s, %s, %s,%s, %s, %s,%s, %s)",
                    (fname, lname, email, sal, job, shift, ph_no, id))
        mysql.connection.commit()
        cur.execute("INSERT INTO emp_address (emp_id,address,city) VALUES (%s, %s, %s)",(id,address,city))
        mysql.connection.commit()
        flash("Employee added successfully!")

        return redirect(url_for('show_emp'))


@app.route("/search_emp", methods=['POST', 'GET'])
@login_required
def search_emp():
    if request.method == "POST":
        id = request.form['srch_emp']
        cur = mysql.connection.cursor()
        cur.execute("select * from employee where emp_id=%s", (id,))
        searched = cur.fetchall()
        if len(searched)==0:
            flash('Employee Not Found')
            return redirect(url_for('show_emp'))
    return render_template('srch_emp.html', admin=data["1"]['username'], emp_data=searched)


@app.route("/show_emp")
@login_required
def show_emp():
    cur = mysql.connection.cursor()
    cur.execute("select employee.emp_id,fname,lname,email,job,shift,sal,ph_no,address,city from employee,emp_address where employee.emp_id=emp_address.emp_id")
    emp_data = cur.fetchall()
    cur.close()
    return render_template('employees.html', emp_data=emp_data, admin=data["1"]['username'])


@app.route("/edit_emp", methods=['POST', 'GET'])
def edit_emp():
    if request.method == "POST":
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        sal = request.form['sal']
        job = request.form['job']
        shift = request.form['shift']
        ph_no = request.form['ph_no']
        address = request.form['addr']
        city = request.form['city']
        id = request.form['id']

        cur = mysql.connection.cursor()
        cur.execute("""
        UPDATE emp_address
        SET address=%s,city=%s WHERE emp_id=%s
        """,(address, city ,id))
        mysql.connection.commit()
        cur.execute("""
               UPDATE employee
               SET fname=%s ,lname=%s, email=%s,sal=%s,job=%s,shift=%s,ph_no=%s
               WHERE emp_id=%s
            """, (fname, lname, email, sal, job, shift, ph_no, id))
        mysql.connection.commit()
        
        flash("Data Updated Successfully")
        
        return redirect(url_for('show_emp'))


@app.route('/del_emp/<string:id_data>', methods=['GET'])
def del_emp(id_data):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM emp_address WHERE emp_id=%s", (id_data,))
    mysql.connection.commit()
    cur.execute("DELETE FROM employee WHERE emp_id=%s", (id_data,))
    mysql.connection.commit()
    flash("Record Has Been Deleted Successfully")
    return redirect(url_for('show_emp'))




@app.route("/orderh", methods=['POST', 'GET'])
@login_required
def orderh():
    cur = mysql.connection.cursor()
    cur.execute("SELECT  * FROM orders ORDER BY(order_id) DESC")
    orders = cur.fetchall()
    cur.close()
    return render_template('order_history.html', admin=data["1"]['username'], orders=orders)


@app.route("/search_order", methods=['POST', 'GET'])
@login_required
def search_order():
    if request.method == "POST":
        id = request.form['srch_order']
        cur = mysql.connection.cursor()
        cur.execute("select * from orders where order_id=%s", (id,))
        searched = cur.fetchall()
    return render_template('srch_orderh.html', admin=data["1"]['username'], orders=searched)


@app.route("/orderp", methods=['POST', 'GET'])
@login_required
def orderp():
    cur = mysql.connection.cursor()
    cur.execute("SELECT  * FROM products")
    product = cur.fetchall()
    cur.close()
    return render_template('place_order.html', admin=data["1"]['username'], product=product)


@app.route("/add_raw", methods=['POST', 'GET'])
def add_raw():
    if request.method == "POST":
        Iname = request.form['Iname']
        qtyb = request.form['qtyb']
        unit = request.form['unit']
        ucost = request.form['ucost']
        id = request.form['id']
        date = datetime.today()
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO raw_material (Iname,qty_bought, m_unit,unit_cost,buy_date,raw_id,current_qty) VALUES (%s, %s, %s,%s, %s,%s,%s)",
                    (Iname, qtyb, unit, ucost, date, id, qtyb))
        mysql.connection.commit()
        flash("Stock added successfully!")
        return redirect(url_for('show_raw'))


@app.route("/edit_raw", methods=['POST', 'GET'])
def edit_raw():
    if request.method == "POST":
        Iname = request.form['Iname']
        qtyb = int(request.form['qtyb'])
        ucost = request.form['ucost']
        id = request.form['id']
        date = datetime.today()
        cur = mysql.connection.cursor()
        cur.execute(
            "select current_qty from raw_material where raw_id=%s", (id,))
        cty = cur.fetchall()
        cty = int(cty[0][0])
        new_cty = cty+qtyb
        cur.execute("""
                UPDATE raw_material SET Iname=%s,qty_bought=%s,current_qty=%s,unit_cost=%s,buy_date=%s
                WHERE raw_id=%s 
        """, (Iname, qtyb, new_cty, ucost, date, id))
        mysql.connection.commit()
        flash("Data Updated Successfully")
    return redirect(url_for('show_raw'))


@app.route("/raw", methods=['POST', 'GET'])
@login_required
def show_raw():
    cur = mysql.connection.cursor()
    cur.execute("SELECT  * FROM raw_material")
    raw_data = cur.fetchall()
    mysql.connection.commit()
    cur.close()
    return render_template('raw_material.html', raw_data=raw_data, admin=data["1"]['username'])


@app.route("/customer", methods=['POST', 'GET'])
@login_required
def cust():
    cur = mysql.connection.cursor()
    cur.execute("SELECT  * FROM customer order by cust_id DESC limit 15 ")
    cust_data = cur.fetchall()
    mysql.connection.commit()
    cur.close()
    return render_template('customers.html', admin=data["1"]['username'], cust_data=cust_data)


@app.route("/search_cust", methods=["POST", "GET"])
@login_required
def search_cust():
    if request.method == "POST":
        ph_no = request.form['srch_cust']
        cur = mysql.connection.cursor()
        cur.execute("select * from customer where ph_no=%s", (ph_no,))
        searched = cur.fetchall()
    if len(searched)==0:
        flash('Customer Not Found')
        return redirect(url_for('cust'))
    return render_template('srch_cust.html', admin=data["1"]['username'], cust_data=searched)


@app.route("/add_cust", methods=['POST', 'GET'])
def add_cust():
    if request.method == "POST":
        fname = request.form['name']
        ph_no = request.form['ph_no']
        addr = request.form['addr']
        cur = mysql.connection.cursor()
        cur.execute("SELECT MAX(cust_id) FROM CUSTOMER")
        new_cust = cur.fetchall()
        mysql.connection.commit()
        newc = new_cust[0][0]+1
        date = datetime.today()
        cur.execute("INSERT INTO customer (cust_id,fname,ph_no,address) VALUES (%s,%s, %s, %s)",
                    (newc, fname, ph_no, addr))
        mysql.connection.commit()
        flash("Customer added successfully!")
        cur.execute("SELECT MAX(order_id) FROM ORDERS")
        new_order = cur.fetchall()
        newo = new_order[0][0]+1
        cur.execute("INSERT INTO orders (cust_id,order_id,order_date) VALUES (%s,%s,%s)",
                    (newc, newo, date))
        mysql.connection.commit()
        return redirect(url_for('cust'))


@app.route("/edit_cust", methods=['POST', 'GET'])
def edit_cust():
    if request.method == "POST":
        fname = request.form['name']
        ph_no = request.form['ph_no']
        addr = request.form['addr']
        id = request.form['id']
        cur = mysql.connection.cursor()
        cur.execute("""
               UPDATE customer
               SET fname=%s,ph_no=%s,address=%s
               WHERE cust_id=%s
            """, (fname, ph_no, addr, id))
        flash("Data Updated Successfully")
        mysql.connection.commit()

        return redirect(url_for('cust'))


@app.route("/cust_order/<string:id>", methods=['POST', 'GET'])
def cust_order(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT MAX(order_id) FROM ORDERS")
    new_order = cur.fetchall()
    newo = new_order[0][0]+1
    date = datetime.today()
    cur.execute("INSERT INTO orders (cust_id,order_id,order_date) VALUES (%s,%s,%s)",
                (id, newo, date))
    mysql.connection.commit()
    return redirect(url_for('orderp'))


@app.route('/bill', methods=['POST', 'GET'])
@login_required
def bill():
    cur = mysql.connection.cursor()
    cur.execute("SELECT products.pname,products.total_price, prod_sell.qty,prod_sell.total from products,prod_sell where (prod_sell.order_id=(SELECT MAX(order_id) FROM ORDERS)) AND (products.prod_id=prod_sell.prod_id)")
    order_details = cur.fetchall()
    cur.execute("select sum(prod_sell.total) AS total_bill from prod_sell,products where (prod_sell.order_id=(SELECT MAX(order_id) FROM ORDERS)) AND (products.prod_id=prod_sell.prod_id)")
    total_bill = cur.fetchall()
    tb = total_bill[0][0]
    return render_template('bill.html', tb=tb, order_details=order_details, admin=data["1"]['username'])


@app.route('/order_confirm', methods=['POST', 'GET'])
def order_confirm():
    stri = ''
    cur = mysql.connection.cursor()
    cur.execute("SELECT products.pname,prod_sell.qty from products,prod_sell where (prod_sell.order_id=(SELECT MAX(order_id) FROM ORDERS)) AND (products.prod_id=prod_sell.prod_id)")
    order_desc = cur.fetchall()
    for desc in order_desc:
        desc = list(desc)
        stri += f"{desc[0]}({desc[1] }) "
    cur.execute("select sum(prod_sell.total) AS total_bill from prod_sell,products where (prod_sell.order_id=(SELECT MAX(order_id) FROM ORDERS)) AND (products.prod_id=prod_sell.prod_id)")
    total_bill = cur.fetchall()
    mysql.connection.commit()
    tb = total_bill[0][0]
    cur.execute(
        "UPDATE ORDERS SET total_bill=%s ,description=%s WHERE ORDER_ID=(SELECT MAX(order_id) FROM ORDERS)", (tb, stri))
    mysql.connection.commit()
    cur.execute("""
        select raw_material.raw_id,cook.qty_used
        from prod_sell
        inner join products
        on (prod_sell.prod_id=products.prod_id) and (prod_sell.order_id=(select max(order_id) from orders))
        inner join cook
        on products.r_id=cook.r_id
        inner join ingredients
        on cook.i_id=ingredients.i_id
        inner join raw_material
        on ingredients.raw_id=raw_material.raw_id
    """)
    data = cur.fetchall()
    for i in range(len(data)):
        raw_id = str(data[i][0])
        qty_used = int(data[i][1])
        cur.execute("""update raw_material set raw_material.current_qty =raw_material.current_qty-%s 
        where raw_material.raw_id=%s""", (qty_used, raw_id))
        mysql.connection.commit()
    cur.close()
    flash("Order placed successfully!")
    return redirect(url_for('dashboard'))


@app.route('/del_order', methods=['POST', 'GET'])
def del_order():
    cur = mysql.connection.cursor()
    cur.execute("select cust_id from orders where order_id=(SELECT MAX(order_id) FROM ORDERS)")
    cust_id=cur.fetchall()
    cust=cust_id[0][0]
    cur.execute("select cust_id from orders where cust_id=%s",(cust,))
    cust_id2=cur.fetchall()
    if len(cust_id2)>=3:
        cur.execute(" DELETE from prod_sell where order_id=(SELECT MAX(order_id) FROM ORDERS)")
        mysql.connection.commit()
        cur.execute(" DELETE from orders where order_id=(SELECT MAX(order_id) FROM ORDERS)")
        mysql.connection.commit()
        print(cust_id2)
        return redirect(url_for('cust'))

    cur.execute(" DELETE from prod_sell where order_id=(SELECT MAX(order_id) FROM ORDERS)")
    mysql.connection.commit()
    cur.execute(" DELETE from orders where order_id=(SELECT MAX(order_id) FROM ORDERS)")
    mysql.connection.commit()
    return redirect(url_for('cust'))   


if __name__ == '__main__':
    app.run(debug=True)
