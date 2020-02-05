using UnityEngine;
using System;
using System.Collections;
using System.Net.Sockets;
using System.Threading;
using System.Collections.Generic;
using System.Text;

//Probably don't need to touch this, use **CerealSendMsg** to send messages basically, don't use the docket SendMessage bc our message is too big and needs to be sent slightly different
public class SocketStarter : MonoBehaviour
{
    public class StateObject
    {
        public Socket workSocket = null;
        public const int BUFFER_SIZE = 4096;
        public byte[] buffer = new byte[BUFFER_SIZE];
        public StringBuilder sb = new StringBuilder();
    }

    Socket connectedSocket = null;
    public bool isAtStartup = true;

    public Queue<string> rcvdRequests = new Queue<string>();

    void Awake()
    {

        try { ClientConnect(); }
        catch (SocketException)
        {
            gameObject.SetActive(false);// = false;
        }
    }


    /// <summary>
    /// ** Called in Awake**
    /// Connects to the server socket
    /// </summary>
    public void ClientConnect()
    {
        //might have to make a outside var to keep track of the connection
        connectedSocket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
        connectedSocket.Connect("127.0.0.1", 3706);
        if (connectedSocket.Connected)
        {
            ReceiveMessage();
        }

        isAtStartup = false;
    }

    public void CloseConnection()
    {
        connectedSocket.Close();
    }

    #region Sending/Rcving Functions
    /// <summary>
    /// Sends message over socket
    /// Note, sends two messages at once, first with the size of the message
    /// second with the actual content (socket needs to understand what it is getting)
    ///
    /// </summary>
    /// <param name="msg"></param>
    public void CerealSendMsg(string msg)
    {
        var msgSize = ASCIIEncoding.ASCII.GetByteCount(msg);
        connectedSocket.Send(BitConverter.GetBytes(msgSize));
        //connectedSocket.Send(ASCIIEncoding.ASCII.GetBytes(msgSize.ToString()));
        connectedSocket.Send(ASCIIEncoding.ASCII.GetBytes(msg));

        ReceiveMessage();
    }

    /// <summary>
    /// sends message over socket - for images
    /// </summary>
    /// <param name="msg"></param>
    public void CerealSendMsg(byte[] msg)
    {
        var picsize = msg.Length;
        //connectedSocket.Send(ASCIIEncoding.ASCII.GetBytes(picsize.ToString()));
        connectedSocket.Send(BitConverter.GetBytes(picsize));
        connectedSocket.Send(msg);
        ReceiveMessage();
    }

    /// <summary>
    /// Call this after sending a message
    /// Communication is like a send and receive- when sending a message expect one back until everything quits
    /// </summary>
    private void ReceiveMessage()
    {
        var stateObj = new StateObject();
        stateObj.workSocket = connectedSocket;
        connectedSocket.BeginReceive(stateObj.buffer, 0, StateObject.BUFFER_SIZE, 0, new AsyncCallback(MessageRcv), stateObj);
        // See MessageReceive
    }

    //This handles the message we get back from the server socket, the isync result - this is when the thread stuff gets weird - but its ok! MainControl brings the stuff back to the main thread
    private void MessageRcv(IAsyncResult asyncResult)
    {
        var bytesReceived = (StateObject)asyncResult.AsyncState;
        connectedSocket.EndReceive(asyncResult);
        var msg = System.Text.Encoding.UTF8.GetString(bytesReceived.buffer).Trim('\0');
        var splitMsgs = msg.Split(',');
        var command = splitMsgs[0];
		rcvdRequests.Enqueue(command);

		var tmpMsg = "";
		int flag=0;
		for(int i =1; i < splitMsgs.Length; i++)
        {
			flag =1;
			if (i!=splitMsgs.Length-1){
			tmpMsg+=splitMsgs[i]+",";
			}
			else{
            tmpMsg+=splitMsgs[i];
			}
		}
		if (flag==1){
			rcvdRequests.Enqueue(tmpMsg);
			
		}
		


    }

//    private void HandleScriptFile(string file)
//    {
//        if(File.Exists(path))
//        {
//            using (StreamReader sr = File.OpenText(path))
//           {
//                string line = "";
//                while((s = sr.ReadLine()) != null)
//                {
//                    Console.WriteLine(s)
//                }
//            }
//        }
//    }

    #endregion







}
