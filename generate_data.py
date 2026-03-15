import os
import random
from faker import Faker
import pandas as pd
from datetime import timedelta


USERS_TO_GENERATE = 12483


def generate_location(fake):
    return {
        'location_id': fake.uuid4(),
        'country_code': 'US',
        'country_full_name': 'United States',
        'city': fake.city(),
        'address': fake.street_address(),
        'zip_code': fake.postcode(),
        'state': fake.state()
    }


def generate_user(fake):
    return {
        'user_id': fake.uuid4(),
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'email': fake.email(),
        'created_at': fake.date_time_between(start_date='-2y', end_date='now')
    }


def pick_next_step(transitions, exit_step=999):
    # Sum up the provided transition probabilities
    total_prob = sum(transitions.values())
    
    # Calculate the probability of exiting
    exit_prob = 1 - total_prob
    
    # Prepare the list of possible steps and their associated probabilities
    steps = list(transitions.keys())
    probs = list(transitions.values())
    
    # Add the exit step if there's remaining probability
    if exit_prob > 0:
        steps.append(exit_step)
        probs.append(exit_prob)
    
    # Use random.choices to select the next step based on the weights
    next_step = random.choices(steps, weights=probs, k=1)[0]
    return next_step



    
def generate_session(fake, user_id, start_date, products):
    steps = {
        1: {
            'event_name': 'page_view',
            'page_url': '/catalog',
            'transitions': {
                2: 0.90,
                3: 0.01,
            },
        },
        2: {
            'event_name': 'page_view',
            'page_url': '/product',
            'transitions': {
                1: 0.01,
                2: 0.40,
                3: 0.01,
                4: 0.08, #### 0.10
            }
        },
        3: {
            'event_name': 'page_view',
            'page_url': '/about_us',
            'transitions': {
                1: 0.01,
                2: 0.10,
            },
        },
        4: {
            'event_name': 'add_to_cart',
            'page_url': '/product/add_to_cart',
            'transitions': {
                2: 0.55,
                5: 0.30 # 0.6
            },
        },
        5: {
            'event_name': 'page_view',
            'page_url': '/checkout',
            'transitions': {
                6: 0.80, # 0.90
            }
        },
        6: {
            'event_name': 'create_order',
            'transitions': {
                1: 0
            }
        },
    }

    user_events = []
    order_items = []
    orders = []

    ORDER_STATUSES = ['pending', 'shipped', 'delivered', 'cancelled']
    PAYMENT_METHODS = ['credit card', 'paypal', 'bank transfer']
    event_time = start_date
    
    current_step = 1
    current_product = random.choice(products)
    products_added_to_cart = []
    
    while current_step <= len(steps):
        product_id = current_product.get('id')
        transitions = steps[current_step].get('transitions')
        
        
        if current_step in [1, 3, 5]:
            #print(current_step, product_id, transitions)
            user_events.append({
                'event_id': fake.uuid4(),
                'user_id': user_id,
                'event_type': steps[current_step].get('event_name'),
                'event_timestamp': event_time,
                'page_url': steps[current_step].get('page_url'),
                'product_id': None,
                'additional_details': None
            })
            current_step = pick_next_step(transitions)
            event_time += timedelta(seconds=random.randint(10, 40), microseconds=random.randint(5, 1000))
        
        elif current_step in [2, 4]:
            #print(current_step, product_id, transitions)
            new_event = {
                'event_id': fake.uuid4(),
                'user_id': user_id,
                'event_type': steps[current_step].get('event_name'),
                'event_timestamp': event_time,
                'page_url': steps[current_step].get('page_url'),
                'product_id': product_id,
                'additional_details': None
            }
            user_events.append(new_event)
            
            if current_step == 4:
                products_added_to_cart.append(product_id)
            if current_step == 2:
                current_product = random.choice(products)
            current_step = pick_next_step(transitions)
            event_time += timedelta(seconds=random.randint(30, 60), microseconds=random.randint(5, 1000))
        
        elif current_step == 6:
            #print(current_step, product_id, transitions)
            order_id = fake.uuid4()
            product_data = [x for x in products if x['id'] == product_id][0]
            total_amount = 0
            for product_id in products_added_to_cart:
                price = product_data.get('price')
                order_items.append({
                    'order_item_id': fake.uuid4(),
                    'order_id': order_id,
                    'product_id': product_id,
                    'quantity': 1,
                    'unit_price': price,
                    'discount': 0,
                    'line_total': price
                })
                total_amount += price
            orders.append({
                'order_id': order_id,
                'user_id': user_id,
                'order_date': event_time,
                'order_status': random.choice(ORDER_STATUSES),
                'payment_method': random.choice(PAYMENT_METHODS),
                'total_amount': total_amount,
                'updated_at': event_time,
            })
            current_step = pick_next_step(transitions)
        

    return {
        'user_events': user_events,
        'order_items': order_items,
        'orders': orders,
    }


def generate_user_and_events(fake, products):
    local_user_events = []
    local_order_items = []
    local_orders = []
    
    # generate user info
    new_user = generate_user(fake)
    new_location = generate_location(fake)
    new_user['location_id'] = new_location['location_id']
    event_time = new_user.get('created_at')
    user_id = new_user.get('user_id')
    
    local_user_events.append({
        'event_id': fake.uuid4(),
        'user_id': user_id,
        'event_type': 'user_sign_up',
        'event_timestamp': event_time,
        'page_url': '/signup',
        'product_id': None,
        'additional_details': None
    })
    
    
    # generate user events, orders and locations
    NUM_USER_SESSIONS = random.choice(range(1, 10))
    for _ in range(1, NUM_USER_SESSIONS + 1):
        new_session = generate_session(fake, user_id, event_time, products)
        local_user_events += new_session.get('user_events')
        local_order_items += new_session.get('order_items')
        local_orders += new_session.get('orders')
    
    return {
        'user': new_user,
        'user_events': local_user_events,
        'order_items': local_order_items,
        'orders': local_orders,
        'locations': [new_location],
    }


def main():
    Faker.seed(42)
    fake = Faker('en_US')
    
    # read products
    df_products = pd.read_csv('input/products.csv')
    all_products = df_products.to_dict(orient='records')

    # starting data
    all_users = []
    all_user_events = []
    all_order_items = []
    all_orders = []
    all_locations = []
    
    # generate users with events, orders and locations for each user

    for _ in range(1, USERS_TO_GENERATE + 1):
        data = generate_user_and_events(fake, all_products)
        all_users.append(data.get('user'))
        all_user_events += data.get('user_events')
        all_order_items += data.get('order_items')
        all_orders += data.get('orders')
        all_locations += data.get('locations')

    df_users = pd.DataFrame(all_users)
    df_user_events = pd.DataFrame(all_user_events)
    df_order_items = pd.DataFrame(all_order_items)
    df_orders = pd.DataFrame(all_orders)
    df_locations = pd.DataFrame(all_locations)

    print('users', len(df_users))
    print('user_events', len(df_user_events))
    print('order_items', len(df_order_items))
    print('orders', len(df_orders))
    print('locations', len(df_locations))

    # Ensure the output directory exists
    os.makedirs('./output', exist_ok=True)
    df_users.to_csv('output/users.csv', index=False)
    df_user_events.to_csv('output/user_events.csv', index=False)
    df_order_items.to_csv('output/order_items.csv', index=False)
    df_orders.to_csv('output/orders.csv', index=False)
    df_locations.to_csv('output/locations.csv', index=False)
    df_products.to_csv('output/products.csv', index=False)

    return {
        'all_users': all_users,
        'all_user_events': all_user_events,
        'all_order_items': all_order_items,
        'all_orders': all_orders,
        'all_locations': all_locations,
    }


if __name__ == "__main__":
    main()
