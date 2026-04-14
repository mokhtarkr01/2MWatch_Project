import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from movies.models import Movie, Genre, Rating, Watchlist

GENRES_DATA = [
    'Action', 'Drama', 'Comedy', 'Thriller', 'Sci-Fi',
    'Romance', 'Horror', 'Animation', 'Documentary', 'Fantasy'
]

MOVIES_DATA = [
    ('The Shawshank Redemption', 1994, 'Frank Darabont', 142, 'Drama'),
    ('The Godfather', 1972, 'Francis Ford Coppola', 175, 'Drama'),
    ('The Dark Knight', 2008, 'Christopher Nolan', 152, 'Action'),
    ('Pulp Fiction', 1994, 'Quentin Tarantino', 154, 'Thriller'),
    ('Schindler\'s List', 1993, 'Steven Spielberg', 195, 'Drama'),
    ('The Lord of the Rings: The Return of the King', 2003, 'Peter Jackson', 201, 'Fantasy'),
    ('Forrest Gump', 1994, 'Robert Zemeckis', 142, 'Drama'),
    ('Inception', 2010, 'Christopher Nolan', 148, 'Sci-Fi'),
    ('Fight Club', 1999, 'David Fincher', 139, 'Thriller'),
    ('The Matrix', 1999, 'The Wachowskis', 136, 'Sci-Fi'),
    ('Goodfellas', 1990, 'Martin Scorsese', 146, 'Drama'),
    ('Interstellar', 2014, 'Christopher Nolan', 169, 'Sci-Fi'),
    ('Parasite', 2019, 'Bong Joon-ho', 132, 'Thriller'),
    ('Spirited Away', 2001, 'Hayao Miyazaki', 125, 'Animation'),
    ('The Silence of the Lambs', 1991, 'Jonathan Demme', 118, 'Thriller'),
    ('Saving Private Ryan', 1998, 'Steven Spielberg', 169, 'Action'),
    ('The Green Mile', 1999, 'Frank Darabont', 189, 'Drama'),
    ('Gladiator', 2000, 'Ridley Scott', 155, 'Action'),
    ('The Prestige', 2006, 'Christopher Nolan', 130, 'Thriller'),
    ('Whiplash', 2014, 'Damien Chazelle', 107, 'Drama'),
    ('La La Land', 2016, 'Damien Chazelle', 128, 'Romance'),
    ('Mad Max: Fury Road', 2015, 'George Miller', 120, 'Action'),
    ('Get Out', 2017, 'Jordan Peele', 104, 'Horror'),
    ('Avengers: Endgame', 2019, 'Anthony & Joe Russo', 181, 'Action'),
    ('Joker', 2019, 'Todd Phillips', 122, 'Drama'),
    ('1917', 2019, 'Sam Mendes', 119, 'Action'),
    ('Once Upon a Time in Hollywood', 2019, 'Quentin Tarantino', 161, 'Drama'),
    ('The Irishman', 2019, 'Martin Scorsese', 209, 'Drama'),
    ('Knives Out', 2019, 'Rian Johnson', 130, 'Thriller'),
    ('Soul', 2020, 'Pete Docter', 100, 'Animation'),
    ('Nomadland', 2020, 'Chloé Zhao', 108, 'Drama'),
    ('Dune', 2021, 'Denis Villeneuve', 155, 'Sci-Fi'),
    ('The Power of the Dog', 2021, 'Jane Campion', 126, 'Drama'),
    ('No Time to Die', 2021, 'Cary Joji Fukunaga', 163, 'Action'),
    ('Spider-Man: No Way Home', 2021, 'Jon Watts', 148, 'Action'),
    ('Everything Everywhere All at Once', 2022, 'Daniels', 139, 'Sci-Fi'),
    ('The Whale', 2022, 'Darren Aronofsky', 117, 'Drama'),
    ('Babylon', 2022, 'Damien Chazelle', 188, 'Drama'),
    ('Oppenheimer', 2023, 'Christopher Nolan', 180, 'Drama'),
    ('Barbie', 2023, 'Greta Gerwig', 114, 'Comedy'),
    ('Poor Things', 2023, 'Yorgos Lanthimos', 141, 'Fantasy'),
    ('Killers of the Flower Moon', 2023, 'Martin Scorsese', 206, 'Drama'),
    ('Past Lives', 2023, 'Celine Song', 106, 'Romance'),
    ('American Fiction', 2023, 'Cord Jefferson', 117, 'Comedy'),
    ('The Holdovers', 2023, 'Alexander Payne', 133, 'Drama'),
    ('May December', 2023, 'Todd Haynes', 117, 'Drama'),
    ('Anatomy of a Fall', 2023, 'Justine Triet', 152, 'Thriller'),
    ('Zone of Interest', 2023, 'Jonathan Glazer', 105, 'Drama'),
    ('Dune: Part Two', 2024, 'Denis Villeneuve', 166, 'Sci-Fi'),
    ('Alien: Romulus', 2024, 'Fede Álvarez', 119, 'Horror'),
]

DESCRIPTIONS = [
    "A gripping tale of resilience, friendship, and the human spirit in the face of adversity.",
    "A masterful exploration of power, loyalty, and the dark heart of the American dream.",
    "An adrenaline-fueled journey that redefines the boundaries of the genre.",
    "A mind-bending narrative that challenges perception and keeps you guessing until the end.",
    "An emotional powerhouse that leaves an indelible mark on the soul.",
    "A visually stunning spectacle combined with rich storytelling and unforgettable characters.",
    "A thought-provoking examination of society, identity, and what it means to be human.",
    "A timeless classic that continues to captivate and inspire audiences worldwide.",
    "An innovative approach to storytelling that pushes creative boundaries.",
    "A deeply moving experience that resonates long after the credits roll.",
]


class Command(BaseCommand):
    help = 'Seeds the database with movies and sample ratings'

    def handle(self, *args, **options):
        self.stdout.write('🎬 Seeding database...')

        # Create genres
        genre_objs = {}
        for g in GENRES_DATA:
            obj, _ = Genre.objects.get_or_create(name=g)
            genre_objs[g] = obj
        self.stdout.write(f'  ✓ {len(genre_objs)} genres created')

        # Create movies
        movies = []
        for title, year, director, duration, genre_name in MOVIES_DATA:
            movie, created = Movie.objects.get_or_create(
                title=title,
                defaults={
                    'release_year': year,
                    'director': director,
                    'duration_min': duration,
                    'description': random.choice(DESCRIPTIONS),
                    'poster_url': f'https://picsum.photos/seed/{abs(hash(title))%1000}/300/450',
                }
            )
            if created:
                movie.genres.add(genre_objs[genre_name])
                # Add a second random genre occasionally
                if random.random() > 0.5:
                    extra = random.choice([g for g in genre_objs.values() if g != genre_objs[genre_name]])
                    movie.genres.add(extra)
            movies.append(movie)
        self.stdout.write(f'  ✓ {len(movies)} movies created')

        # Create sample users
        usernames = ['alice', 'bob', 'carol', 'dave', 'eve', 'frank', 'grace', 'henry']
        users = []
        for uname in usernames:
            user, created = User.objects.get_or_create(username=uname)
            if created:
                user.set_password('password123')
                user.save()
            users.append(user)
        self.stdout.write(f'  ✓ {len(users)} sample users created')

        # Generate realistic ratings (not all movies rated by all users)
        rating_count = 0
        for user in users:
            # Each user rates 15-35 random movies
            n_ratings = random.randint(15, 35)
            rated_movies = random.sample(movies, min(n_ratings, len(movies)))

            # Create user "taste profile" - they prefer certain genres
            fav_genre = random.choice(list(genre_objs.values()))

            for movie in rated_movies:
                if not Rating.objects.filter(user=user, movie=movie).exists():
                    # Bias score toward 4-5 if movie matches preferred genre
                    if fav_genre in movie.genres.all():
                        score = random.choices([1, 2, 3, 4, 5], weights=[2, 5, 15, 40, 38])[0]
                    else:
                        score = random.choices([1, 2, 3, 4, 5], weights=[8, 15, 30, 30, 17])[0]
                    Rating.objects.create(user=user, movie=movie, score=score)
                    rating_count += 1

        self.stdout.write(f'  ✓ {rating_count} ratings generated')
        self.stdout.write(self.style.SUCCESS('\n✅ Database seeded successfully!'))
        self.stdout.write('  Superuser: admin / admin123')
        self.stdout.write('  Sample users: alice, bob, carol, dave, eve, frank, grace, henry / password123')
