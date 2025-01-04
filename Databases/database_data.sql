-- Active: 1728309488095@@127.0.0.1@3306@event_management
INSERT INTO `User` (username, email, password, bio) VALUES
('Abdulkadir', 'abdulkadirkk42@gmail.com', 'password123', 'Doğa sever'),
('Ahmet', 'ahmett52@gmail.com', 'password456', 'Sporcu'),
('Emre', 'emre34@gmail.com', 'password789', 'Yazılım geliştiricisi'),
('Serpil', 'serpil@gmail.com', 'password101', 'Kitap okumayı severim'),
('Arda', 'ardagüler@gmail.com', 'password112', 'Sinema tutkunu ve gezgin'),
('Ayşe', 'ayse@gmail.com', 'password131', 'Usmanım'),
('Zeynep', 'zeyno@gmail.com', 'password415', 'Sosyal medya ve dijital pazarlama uzmanı'),
('Arda Utku', 'ardautku@gmail.com', 'pw124235346', 'Profesyonel tenis oyuncusu'),
('Efekan', 'efkn@gmail.com', 'pssw234wetr36', 'Kitap kurdu'), 
('Mete', 'egmt@gmail.com', '12345', 'İlkel teknolojiler meraklısı'),
('Utku', 'utku@gmail.com', 'sst3424146', 'CEO @qFin');

use event_management;


INSERT INTO `Group` (group_name, group_description, created_by) VALUES
('Trekking', 'Her hafta sonu doğa yürüyüşleri düzenleriz.', 1),
('Okçuluk Kulübü', 'Okçuluk ve her şey', 3),
('Müzik ve Konserler', 'Canlı müzik geceleri, konserler ve dahası', 7),
('Kitap Önerileri', 'Kitap okumadan yaşamın eksik kalacağını düşünen herkesi buluşturmak ümidiyle...', 9),
('Borsa Istanbul Analiz', 'Anlık borsa analizleri', 11);


INSERT INTO `Membership` (user_id, group_id, user_role) VALUES
(1, 1, 'Admin'),
(2, 1, 'Member'),
(3, 2, 'Member'),
(4, 3, 'Admin'),
(5, 2, 'Guest'),
(6, 3, 'Member'),
(7, 1, 'Admin'),
(9, 4, 'Admin'),
(1, 4, 'Member'),
(2, 4, 'Member'), 
(3, 4, 'Member'),
(11, 5, 'Admin'), 
(2, 5, 'Member'),
(6, 5, 'Member');



INSERT INTO `Event` (group_id, event_name, event_description, event_date, event_location) VALUES
(1, 'Doğa Yürüyüşü - Aralık', 'Kışın en güzel doğa yürüyüşü', '2026-12-10', 'Çamlıca Tepesi'),
(2, 'Okçuluk Turnuvası', 'Eğlenceli bir okçuluk turnuvası', '2026-12-15', 'Atatürk Ormanı'),
(3, 'Yeni Yıl Konseri', 'Yılbaşı öncesi bir konser etkinliği', '2026-12-25', 'Beyoğlu Konser Salonu'),
(4, '41. Uluslararası Kitap Fuarı', 'Uluslararası Kitap Fuarı', '2026-11-19', 'TÜYAP Fuar ve Kongre Merkezi');



INSERT INTO `Event_Attendance` (user_id, event_id, event_status) VALUES
(1, 1, 'Attended'),
(2, 1, 'Attended'),
(3, 2, 'Attended'),
(4, 3, 'Attended'),
(5, 2, 'Attended'),
(6, 3, 'Attended'),
(7, 1, 'Attended'),
(9, 4, 'Attended'),
(3, 4, 'Not Attended');



INSERT INTO `Feedback` (user_id, event_id, rating, feedback) VALUES
(1, 1, 5, 'Harika bir etkinlikti, çok keyif aldım!'),
(2, 1, 4, 'Güzel bir yürüyüş, ancak biraz daha fazla rehber olabilir.'),
(3, 2, 3, 'Katılamadım ama etkinlik fikri hoştu.'),
(4, 3, 5, 'Konser mükemmeldi, harika bir atmosfer vardı.'),
(5, 2, 4, 'Okçuluk turnuvası çok eğlenceliydi, daha fazla katılım beklerdim.'),
(6, 3, 5, 'Yeni yıl konseri harikaydı, müzik çok iyiydi.'),
(7, 1, 2, 'Yürüyüş güzeldi ama hava soğuktu.'),
(9, 4, 5, 'Favori yazarımla nihayet tanışabildim, harika bir insan!');



INSERT INTO `Message_Board` (group_id, user_id, user_message) VALUES
(1, 1, 'Doğa yürüyüşü için hazırlıklara başladık, katılacak olan var mı?'),
(2, 3, 'Okçuluk turnuvası için kayıtlar başladı, herkesi bekliyoruz!'),
(3, 4, 'Yeni yıl konserine bilet almayı unutmayın, yerler sınırlı!');



INSERT INTO `Tag` (tag_name) VALUES
('Doğa'),
('Spor'),
('Müzik'),
('Yeni Yıl'),
('Finans'),
('Kitap');



INSERT INTO `Event_Tag` (event_id, tag_id) VALUES
(1, 1),
(2, 2),
(3, 3),
(3, 4),
(4, 6);
