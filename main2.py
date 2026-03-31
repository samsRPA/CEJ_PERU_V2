import asyncio


class KeyCEJRepository:
    def __init__(self):
        pass

    async def get_keys_cej(self, conn):
        try:

            query = f""" 
             SELECT     PI.PROCESO_ID,
                            PI.INSTANCIA_RADICACION,
                            D.DESPACHO_NOMBRE,
                            CASE 
                            WHEN D.DESPACHO_NOMBRE LIKE '%DE PAZ%' THEN 'JUZGADO DE PAZ LETRADO'
                            ELSE 
                                'JUZGADO ESPECIALIZADO'
                            END INSTANCIA,
                            CASE 
                            WHEN D.DESPACHO_NOMBRE LIKE '%CIVIL%' THEN 'CIVIL'
                                WHEN D.DESPACHO_NOMBRE LIKE '%COMERCIAL%' THEN 'COMERCIAL'
                                WHEN D.DESPACHO_NOMBRE LIKE '%DE PAZ%' THEN 'CIVIL'
                                WHEN D.DESPACHO_NOMBRE LIKE '%FAMILIA%' THEN 'FAMILIA'
                            END ESPECIALIDAD,
                            F_REPLACE_CHAR (VM.DEMANDANTE) AS DEMANDANTE,
                                F_REPLACE_CHAR (VM.DEMANDADO) AS DEMANDADO
                    FROM PROCESOS_INSTANCIAS PI, DESPACHOS D , VM_PROCESOS VM , PROCESOS_CLIENTES PC
                    WHERE  PI.PROCESO_ID = VM.PROCESO_ID   
                        AND PI.DESPACHO_ID = D.DESPACHO_ID
                        AND PC.PROCESO_ID = PI.PROCESO_ID
                        AND VM.PROCESO_ID = PC.PROCESO_ID
                        AND D.LOCALIDAD_ID IN (    SELECT LOCALIDAD_ID
                                                        FROM LOCALIDADES
                                                CONNECT BY PRIOR LOCALIDAD_ID = LOCALIDAD_PADRE
                                                START WITH LOCALIDAD_ID = 589)           
                        AND LENGTH(PI.INSTANCIA_RADICACION) > 12 
                        AND   PI.INSTANCIA_RADICACION IN (
                            
'12313-2022-10-1801-SP-LA-18',
'16738-2023-0-1801-JR-LA-08',
'00325-2024-0-0701-JR-LA-02',
'01853-2020-2-2001-JR-LA-08',  
'10081-2018-0-1801-JR-LA-03',
'01713-2018-0-1815-JP-LA-05',
'10355-2018-0-1801-JR-LA-02',
'05535-2018-0-1601-JR-LA-07',
'06717-2017-0-1601-JR-LA-09',
'06935-2018-0-1601-JR-LA-01',
'01056-2018-0-2001-JP-LA-05',
'02661-2017-0-1801-JR-LA-07',
'09521-2018-0-1601-JR-LA-07',
'09567-2018-0-1601-JR-LA-07',
'00562-2019-0-1601-JR-LA-07',
'00562-2019-0-1601-JR-LA-07',
'01042-2019-0-1601-JR-LA-09',
'03132-2019-0-1801-JR-LA-03',
'06466-2019-0-1801-JR-LA-03',
'17055-2019-0-1801-JR-LA-12',
'01125-2020-0-1601-JR-LA-07',
'02459-2020-0-1601-JR-LA-08',
'01704-2022-0-1801-JR-LA-08',
'01712-2022-0-1801-JR-LA-08',
'01709-2022-0-1801-JR-LA-09',
'01711-2022-0-1801-JR-LA-09',
'01700-2022-0-1801-JR-LA-09',
'01705-2022-0-1801-JR-LA-09',
'01713-2022-0-1801-JR-LA-09',
'01706-2022-0-1801-JR-LA-08',
'12663-2022-0-1801-JR-LA-14',
'13108-2022-0-1801-JR-LA-02',
'06889-2019-0-1601-JR-LA-06',
'01708-2022-0-1801-JR-LA-08',
'01714-2022-0-1801-JR-LA-08',
'12675-2022-0-1801-JR-LA-18',
'05436-2023-0-1801-JR-LA-07',
'05958-2023-3-1801-JR-LA-10',
'01277-2019-0-0601-JR-LA-02',
'00499-2019-0-2501-JR-LA-03',
'03543-2019-0-2501-JR-LA-02',
'02646-2021-0-2501-JR-LA-09',
'01640-2021-0-2501-JR-LA-03',
'02751-2021-0-2501-JR-LA-09',
'01789-2021-0-2501-JR-LA-09',
'02788-2021-0-2501-JR-LA-09',
'03188-2021-0-2501-JR-LA-03',
'01615-2021-0-2501-JR-LA-08',
'00798-2022-0-2501-JR-LA-08',
'01682-2021-0-2501-JR-LA-06',
'01743-2021-0-2501-JR-LA-09',
'00186-2019-0-1408-JR-LA-01',
'02751-2022-0-1801-JR-LA-11',
'03203-2023-0-1815-JP-LA-08',
'22469-2023-0-1801-JR-LA-02',
'06294-2024-0-1864-JR-LA-08',
'09784-2018-0-1801-JR-LA-75',
'12981-2017-0-1801-JR-LA-16',
'17258-2018-0-1801-JR-LA-25',
'20662-2018-0-1801-JR-LA-01',
'26325-2019-0-1801-JR-LA-74',
'06744-2020-0-1801-JR-LA-03',
'01053-2015-0-1809-JP-LA-05',
'04299-2019-0-1809-JP-LA-04',
'929-2024-0-2001-JR-LA-01',
'05450-2023-0-2001-JR-LA-03',
'05450-2023-0-2001-JR-LA-03',
'05450-2023-0-2001-JR-LA-03',
'05450-2023-0-2001-JR-LA-03',
'00929-2024-0-2001-JR-LA-01',
'00929-2024-0-2001-JR-LA-01',
'00929-2024-0-2001-JR-LA-01',
'01853-2020-0-2001-JR-LA-08',
'06534-2018-0-1601-JR-LA-04',
'07115-2018-0-1601-JR-LA-10',
'06964-2018-0-1601-JR-LA-02',
'06966-2018-0-1601-JR-LA-04',
'06937-2018-0-1601-JR-LA-03',
'07130-2018-0-1601-JR-LA-08',
'06968-2018-0-1601-JR-LA-01',
'07034-2018-0-1601-JR-LA-02',
'07080-2018-0-1601-JR-LA-01',
'00535-2019-0-1601-JR-LA-07',
'00242-2019-0-1601-JR-LA-07',
'00756-2019-0-1601-JR-LA-08',
'01336-2019-0-1601-JR-LA-01',
'01990-2019-0-1601-JR-LA-03',
'02536-2019-0-1601-JR-LA-03',
'02423-2019-0-1601-JR-LA-04',
'02537-2019-0-1601-JR-LA-07',
'00534-2019-0-1601-JR-LA-02',
'02665-2020-0-1601-JR-LA-10'
)
                                        
            """
            
            async with conn.cursor() as cursor:
                await cursor.execute(query)
                # extraemos solo el primer elemento de cada tupla
                return await cursor.fetchall()  
         
        except Exception as error:
            raise error

    async def get_key_cej(self,conn, radicado):
        try:

            query = f""" 
                SELECT     PI.PROCESO_ID,
                            PI.INSTANCIA_RADICACION,
                            D.DESPACHO_NOMBRE,
                            CASE 
                            WHEN D.DESPACHO_NOMBRE LIKE '%DE PAZ%' THEN 'JUZGADO DE PAZ LETRADO'
                            ELSE 
                                'JUZGADO ESPECIALIZADO'
                            END INSTANCIA,
                            CASE 
                            WHEN D.DESPACHO_NOMBRE LIKE '%CIVIL%' THEN 'CIVIL'
                                WHEN D.DESPACHO_NOMBRE LIKE '%COMERCIAL%' THEN 'COMERCIAL'
                                WHEN D.DESPACHO_NOMBRE LIKE '%DE PAZ%' THEN 'CIVIL'
                                WHEN D.DESPACHO_NOMBRE LIKE '%FAMILIA%' THEN 'FAMILIA'
                            END ESPECIALIDAD,
                            F_REPLACE_CHAR (VM.DEMANDANTE) AS DEMANDANTE,
                                F_REPLACE_CHAR (VM.DEMANDADO) AS DEMANDADO
                    FROM PROCESOS_INSTANCIAS PI, DESPACHOS D , VM_PROCESOS VM , PROCESOS_CLIENTES PC
                    WHERE  PI.PROCESO_ID = VM.PROCESO_ID   
                        AND PI.DESPACHO_ID = D.DESPACHO_ID
                        AND PC.PROCESO_ID = PI.PROCESO_ID
                        AND VM.PROCESO_ID = PC.PROCESO_ID
                        AND D.LOCALIDAD_ID IN (    SELECT LOCALIDAD_ID
                                                        FROM LOCALIDADES
                                                CONNECT BY PRIOR LOCALIDAD_ID = LOCALIDAD_PADRE
                                                START WITH LOCALIDAD_ID = 589)           
                        AND LENGTH(PI.INSTANCIA_RADICACION) > 12
                        and PI.INSTANCIA_RADICACION = '{radicado}'  
                       
                        

            """
            
            async with conn.cursor() as cursor:
                await cursor.execute(query)
                # extraemos solo el primer elemento de cada tupla
                return await cursor.fetchall()  
         
        except Exception as error:
            raise error
