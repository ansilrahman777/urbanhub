from django.shortcuts import render,redirect, get_object_or_404
from django.http import HttpResponse
from .models import Product,Category,User,Cart,CartItem,Variation,Address,Order,OrderProducts,Payment
from django.contrib import messages,auth
from .forms import SignupForm,ProfileEditForm
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.cache import cache_control
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import EmptyPage,PageNotAnInteger,Paginator
import requests
#activation
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage



@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def user_index(request):
    products = Product.objects.all().filter(is_available=True)

    context = {
        'products': products,
    }
    return render(request,'user_temp/user_index.html',context)

def user_about(request):
    return render(request,'user_temp/user_about.html') 

def user_contact(request):
    return render(request,'user_temp/user_contact.html') 

# ----------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------login-----------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------

@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def user_login(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method=='POST':
        email=request.POST['email']
        password=request.POST['password']

        print(f"Received email: {email}")
        print(f"Received password: {password}")

        user = auth.authenticate(email=email,password=password)
        print("User:", user)

        if user is not None:
            try:
                cart=Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item =CartItem.objects.filter(cart=cart)
                    product_variation=[]
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    cart_item = CartItem.objects.filter(user=user)
                    ex_var_list=[]
                    id=[]
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)

                    for pr in product_variation:
                        if pr in ex_var_list:
                            index =ex_var_list.index(pr)
                            item_id=id[index]
                            item =CartItem.objects.get(id=item_id)
                            item.quantity +=1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
            except:
                pass

            if user.is_blocked:
                messages.error(request, "Your account is blocked. Please contact the administrator.")
            else:
                auth.login(request, user)
                messages.success(request, "Login successful")
                url=request.META.get('HTTP_REFERER')
                try:
                    query=requests.utils.urlparse(url).query
                    params =dict(x.split('=')for x in query.split('&'))
                    if 'next'  in params :
                        nextPage=params['next']
                        return redirect(nextPage)                    
                except:
                    return redirect('/')                
        else:
            messages.error(request, "Invalid credentials")

    return render(request, 'user_temp/user_login.html')

@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def user_sign_up(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method=='POST':
        form = SignupForm(request.POST)
        if form.is_valid():

            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            mobile = form.cleaned_data['mobile']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]

            user = User.objects.create_user(first_name=first_name,last_name=last_name,email=email,username=username,mobile=mobile,password=password)
            # user.save()



            current_site = get_current_site(request)
            mail_subject = 'please activate your account'
            message =render_to_string('user_temp/user_email_verfication.html',{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            to_email = email
           
            send_email =EmailMessage(mail_subject,message,to=[to_email])
            send_email.send()


            messages.success(request,'signup successfull, activation link is sent to the registerd email ')
            return redirect('user_login')

    else:
        form = SignupForm()
    context = {
        'form' : form,
    }

    return render(request, 'user_temp/user_sign_up.html',context)

@cache_control(no_cache=True,must_revalidate=True,no_store=True) 
def activate(request,uidb64,token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user,token):
        user.is_active = True
        user.save()
        messages.success(request,'activation successfull')
        return redirect('user_login')
    else:
        messages.error(request,'invalid activation link')
        return redirect('user_sign_up')

@login_required(login_url='user_login')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def user_logout(request):
    auth.logout(request)
    messages.success(request,'logout successfull')
    return redirect('user_login')


def user_forgot_password(request):
    if request.method=='POST':
        email = request.POST['email']
        if User.objects.filter(email=email).exists():
            user =User.objects.get(email__exact=email)

            current_site = get_current_site(request)
            mail_subject = 'Reset your password'
            message =render_to_string('user_temp/user_reset_password_email.html',{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            to_email = email
            send_email =EmailMessage(mail_subject,message,to=[to_email])
            send_email.send()

            messages.success(request,'Your password reset link send to registered email')
            return redirect('user_login')


        else:
            messages.error(request,'User doesnot exixts!!')
            return redirect('user_forgot_password')

    return render(request,'user_temp/user_forgot_password.html')


def user_reset_password_validate(request,uidb64,token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user,token):
        request.session['uid'] =uid
        messages.success(request,'Reset your password')
        return redirect('user_reset_password')
    else:
        messages.error(request,'try again!! link expired')
        return redirect('user_forgot_password')

    return render(request,'user_temp/user_reset_password.html')

def user_reset_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = User.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            request.session.flush()
            messages.success(request,'Reset password success')
            request.session.flush()
            return redirect('user_login')
        else:
            messages.error(request,'password doesnot match')
            return redirect('user_reset_password') 

    else:
        return render(request,'user_temp/user_reset_password.html')

# ----------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------shop------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------

@never_cache
def user_shop(request, category_slug=None):
    category = None
    products = None
    
    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories,is_available=True)
        paginator = Paginator(products,6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    else:
        products = Product.objects.all().filter(is_available=True).order_by('id')   
        paginator = Paginator(products,6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()


    context = {
        'products': paged_products,
        'product_count': product_count,
        'selected_category': category,  
    }

    return render(request, 'user_temp/user_shop.html', context)

def search(request):
    keyword = request.GET.get('keyword') 

    products = Product.objects.none()  

    if keyword:
        products = Product.objects.order_by('id').filter(product_name__icontains=keyword)

    context = {
        'products': products,
    }

    return render(request, 'user_temp/user_shop.html', context)

# ----------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------product------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------

@never_cache
def user_product_detail(request,category_slug,product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug,slug=product_slug)
        
    except Exception as e:
        raise e

    context = {
        'single_product': single_product,
    }
    return render(request,'user_temp/user_product_detail.html',context)

# ----------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------cart----------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart =request.session.create()
    return cart


def user_add_cart(request, product_id):
    current_user=request.user
    product = Product.objects.get(id=product_id)
    if current_user.is_authenticated:
        product_variation=[]
        if request.method == 'POST':
            for item in request.POST:
                key = item 
                value = request.POST[key]
                print(f"Key: {key}, Value: {value}")
                try:
                    variation = Variation.objects.get(product=product,variation_category__iexact=key,variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass
        
        is_cart_item_exists = CartItem.objects.filter(product=product,user=current_user).exists()
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product,user=current_user)
            ex_var_list=[]
            id=[]
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            if product_variation in ex_var_list:
                index =ex_var_list.index(product_variation)
                item_id=id[index]
                item =CartItem.objects.get(product=product,id=item_id)
                item.quantity +=1
                item.save()
            else:
                item =CartItem.objects.create(product=product,quantity=1,user=current_user)
                if len(product_variation)>0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else:
            cart_item=CartItem.objects.create(
                product=product,
                quantity=1,
                user=current_user,
            )
            if len(product_variation)>0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        return redirect('user_cart')
    #if user is not authenticated (same code for both)  
    else:
        product_variation=[]
        if request.method == 'POST':
            for item in request.POST:
                key = item 
                value = request.POST[key]
                print(f"Key: {key}, Value: {value}")
                try:
                    variation = Variation.objects.get(product=product,variation_category__iexact=key,variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass
            
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id=_cart_id(request)
            )
            cart.save()
        is_cart_item_exists = CartItem.objects.filter(product=product,cart=cart).exists()

        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product,cart=cart)

            ex_var_list=[]
            id=[]
            for item in cart_item:

                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)

            if product_variation in ex_var_list:
                index =ex_var_list.index(product_variation)
                item_id=id[index]
                item =CartItem.objects.get(product=product,id=item_id)
                item.quantity +=1
                item.save()
                
            else:
                item =CartItem.objects.create(product=product,quantity=1,cart=cart)
                if len(product_variation)>0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else:
            cart_item=CartItem.objects.create(
                product=product,
                quantity=1,
                cart=cart,
            )
            if len(product_variation)>0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        return redirect('user_cart')


def user_remove_cart(request, product_id,cart_item_id):

    
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get( product=product, user=request.user ,id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request ))
            cart_item = CartItem.objects.get( product=product, cart=cart ,id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('user_cart')


def user_remove_cart_item(request, product_id,cart_item_id):

    
    product = get_object_or_404(Product, id=product_id)
    if request.user.is_authenticated:
        cart_item =  CartItem.objects.get( product=product, user=request.user,id=cart_item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item =  CartItem.objects.get( product=product, cart=cart,id=cart_item_id)
    cart_item.delete()

    return redirect('user_cart')

def user_cart(request,total=0,quantity=0,cart_items=None):
    try:
        if request.user.is_authenticated:
            cart_items=CartItem.objects.filter(user=request.user, is_active=True)
        else:  
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items=CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
    except Cart.DoesNotExist:
        pass

    context={
        'total':total,
        'quantity':quantity,
        'cart_items':cart_items,
    }

    return render(request,'user_temp/user_cart.html',context)

# ----------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------profile-----------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------

@login_required(login_url='user_login')
def user_profile(request):
    return render(request,'user_temp/user_profile.html')

@login_required(login_url='user_login')
def user_profile_edit(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('user_profile')
        else:
            print(form.errors) 
            messages.error(request, 'Error updating your profile. Please check the form data.')
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, 'user_temp/user_profile_edit.html', {'form': form})


@login_required(login_url='user_login')
@cache_control(no_cache=True,must_revalidate=True,no_store=True) 
def user_change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = User.objects.get(username__exact=request.user.username)

        if new_password==confirm_password:
            if not len(new_password) < 8: 
                success = user.check_password(current_password)
                if success:
                    user.set_password(new_password)
                    user.save()

                    messages.success(request, 'Password changed successfully.')
                    return redirect('user_profile')

                else:
                    messages.error(request, 'enter a valid current password')
                    return redirect('user_change_password')
            else:
                messages.error(request, 'Password must be at least 8 characters long')
                return redirect('user_change_password')
        else:
            messages.error(request, 'Password doesnot match')
            return redirect('user_change_password')

    return render(request,'user_temp/user_change_password.html')

# ----------------------------------------------------------------------------------------------------------------
# ----------------------------------------------address---------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------
@login_required(login_url='user_login')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def user_address(request):
    state_choices = Address.STATE_CHOICES
    addresses = Address.objects.filter(user_id=request.user.id)

    context = {
        'state_choices': state_choices,
        'addresses': addresses,
    }
    return render(request,'user_temp/user_address.html',context)

@login_required(login_url='user_login')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def user_add_address(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address_line_1 = request.POST.get('address_line_1')
        address_line_2 = request.POST.get('address_line_2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pin = request.POST.get('pin')
        country = request.POST.get('country')
        phone = request.POST.get('phone')
        is_default = request.POST.get('is_default')
        is_default = is_default == "on"

        user = request.user

        address = Address(
            user_id=user,
            first_name=first_name,
            last_name=last_name,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            city=city,
            state=state,
            pin=pin,
            country=country,
            phone=phone,
            is_default=is_default
        )
        if len(phone) != 10:
            messages.warning(request,'Mobile number must be 10 digits !')
            return redirect('user_address')
        if len(pin) > 6:
            messages.warning(request,'Invalid Pincode !')
            return redirect('user_address')
        if not pin.isdigit():
            messages.warning(request, 'Invalid Pincode! Please enter a numeric PIN code.')
            return redirect('user_address')
        
    
        address.save()
        messages.success(request,'Address added')
        return redirect('/user_address')

    state_choices = Address.STATE_CHOICES  
    context = {
        'state_choices': state_choices,
    }
    
    return render(request,'user_temp/user_address.html',context)

@login_required(login_url='user_login')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def user_edit_address(request,id):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address_line_1 = request.POST.get('address_line_1')
        address_line_2 = request.POST.get('address_line_2')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pin = request.POST.get('pin')
        country = request.POST.get('country')
        phone = request.POST.get('phone')
        is_default = request.POST.get('is_default')

        user = request.user
        save_address = Address.objects.get(id=id)
 
        save_address.first_name=first_name
        save_address.last_name=last_name
        save_address.address_line_1=address_line_1
        save_address.address_line_2=address_line_2
        save_address.city=city
        if state:
            save_address.state=state
        save_address.pin=pin
        save_address.country=country
        save_address.phone=phone
        save_address.is_default = is_default == "on"

        if len(phone) != 10:
            messages.warning(request,'Mobile number must be 10 digits !')
            return redirect('user_profile')
        if len(pin) > 6:
            messages.warning(request,'Invalid Pincode !')
            return redirect('user_profile')
        if not pin.isdigit():
            messages.warning(request, 'Invalid Pincode! Please enter a numeric PIN code.')
            return redirect('user_address')
        
        save_address .save()
        return redirect('user_address')

    return render(request,'user_temp/user_address.html')
@login_required(login_url='user_login')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def user_remove_address(request, id):
    try:
        address = Address.objects.get(id=id)
        address.delete()
        messages.success(request, 'Address removed successfully.')
    except Address.DoesNotExist:
        messages.error(request, 'Address not found.')
    
    return redirect('user_address')

@login_required(login_url='user_login')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def user_default_address(request,id):
    address = get_object_or_404(Address, id=id)
    addresses=Address.objects.filter().exclude(id=id)
    if address.is_default:
        address.is_default=False
        for add in addresses:
            add.is_default=True
            address.save()
    else:
        address.is_default=True
        for add in addresses:
            add.is_default=False
            add.save()
    address.save()

    return render(request,'user_temp/user_address.html')

# ----------------------------------------------------------------------------------------------------------------
# ------------------------------------------------checkout--------------------------------------------------------
# ----------------------------------------------------------------------------------------------------------------

@login_required(login_url='user_login')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def user_checkout(request,total=0,quantity=0,cart_items=None):

    addresses = Address.objects.filter(user_id=request.user.id)
    try:
        if request.user.is_authenticated:
            cart_items=CartItem.objects.filter(user=request.user, is_active=True)
        else:  
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items=CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total +=(cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
    except ObjectDoesNotExist:
        pass

    context={
        'total':total,
        'quantity':quantity,
        'cart_items':cart_items,
        'addresses': addresses,
    }

    return render(request,'user_temp/user_checkout.html',context)

@login_required(login_url='user_login')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def user_place_order(request):
    current_user=request.user

    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <=0:
        return redirect('user_shop')



    return render(request,'user_temp/user_place_order.html')