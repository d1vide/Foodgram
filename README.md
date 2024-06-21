# Foodgram
## Описание проекта:
«Фудграм» — сайт, на котором пользователи могут публиковать свои рецепты,
добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям также будет доступен сервис «Список покупок». Он позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд
## Стек технологий:
* ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
* ![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
* ![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)
* ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
* ![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
* ![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white)
* ![Gunicorn](https://img.shields.io/badge/gunicorn-%298729.svg?style=for-the-badge&logo=gunicorn&logoColor=white)
* ![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)
## Как развернуть проект:
Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://github.com/d1vide/foodgram.git
```
Создать файл .env по примеру из файла <a> href="https://github.com/d1vide/foodgram/blob/main/.env.example">.env.example</a>
Запустить docker-compose файл:
```
docker compose -f docker-compose.production.yml up -d
```
Далее сделать и применить миграции, а также собрать статику:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py makemigrations
```
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
```

### Проект доступен по адресу:
```
https://testsite.sytes.net/recipes
```

